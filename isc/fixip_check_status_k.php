<?php
  /*
    請使用UTF-8 without BOM編碼
  */
  include_once('common.inc.php');
  /*function logf($s)
  {
    $logname="fixip_check_status_leon";
    $outf = fopen('/ap/www/log/coss/'.$logname.'_'.date('Ym').'.log','a');

    $hostip = getenv("REMOTE_ADDR");
    $url = $_SERVER['QUERY_STRING'];
    fprintf($outf, "[%s,%s,%s]%s\n", date('Y/m/d H:i:s'), $hostip, $url, $s);
    fclose($outf);
  }*/
  
  $now = date("Y-m-d H:i:s");
  echo "START: $now ";echo "<br>\n";

  
  $nms = GetDBH('CNIS');
  $database_array = array("TFM");
  //--------震江(1)----------s
  $ms0210_ip = array();
  foreach($database_array as $db){
    $dbh = null;
    switch ($db) {
      case 'CG':
        $dbh = GetDBH('CGCossMS');
        break;
      case 'TFM':
        $dbh = GetDBH('TFMCossMS');
        break;
      case 'KBRO':
        $dbh = GetDBH('kbroCossMS');
        break;  
    }
    $sql = "select a.companyno as COMPANYNO,a.subsid as SUBSID,b.notinhSubsid as IP,b.chargename as CHARGENAME from ms0200 a with (nolock)
          inner join (
          select companyno,subsid,notinhSubsid,chargename,disctime from ms0210 with (nolock)
          where chargename like '%付費固定%'  and (  (companyno like '___' ) or (companyno like 'DE-___' and disctime >= getdate())  )
          ) b on b.companyno=a.companyno and b.subsid=a.subsid
          where len(a.companyno)=3 and  a.servicename in ('2 CM','5 FTTB','7 EOC') and substring(a.custstatus,1,1) in ('0','1','6','8','9','7','B')
    ";
    $sth = mssql_query($sql,$dbh);
    while($row = mssql_fetch_assoc($sth)){
      $ms0210_ip[$row['SUBSID']][$row['CHARGENAME']] = $row;
    }
  }
  //--------震江(1)----------e
  
  //--------oci----------s
  $cnr_fixip_coss_arr = array();
  $sql = "select a.subsid,a.companyno,a.ip,a.chargename,a.pay,a.mac,b.cnr_id from cnr_fixip_coss a  left join cnr_queue b  on  a.cnr_id = b.sid where a.pay is not null and a.companyno in ('101','103','104','300','701')";
  $sth = oci_parse($nms,$sql);
  oci_execute($sth);
  while($row = oci_fetch_assoc($sth)){
    $cnr_fixip_coss_arr[$row['SUBSID']][$row['CHARGENAME']] = $row;
  }
  //--------oci----------e
  
  //--------鎮江 oci 比較----------s
  /*$result1 = 比對兩個名單, 以震江(1)的名單為主, 沒在名單中的要做以下的事情
    $result2 = 比對兩個名單, 以震江(1)的名單為主, 有在名單中的要做以下的事情*/
  $result1 = $result2 = array();
  foreach($cnr_fixip_coss_arr as $subsid=> $item){
    if($ms0210_ip[$subsid]){
      foreach($item as $chargename =>$item2){
        if($ms0210_ip[$subsid][$chargename] ){
          $result2[] = $item2;
        }else{
          $result1[] = $item2;
        } 
      }
    }else{
      foreach($item as $item2){
        $result1[] = $item2;
      }
    }
  }
  //--------鎮江 oci 比較----------e 
   //
   //
  //確認全部的付費固定IP狀態-----s
  $result1_ms = array();
  foreach($result1 as $item){
    if($item['COMPANYNO'] == '106'){
      $result1_ms['CG'][] = $item['SUBSID'];
    }else if (preg_match("/^(101|103|104|300|701|500)$/i", $item['COMPANYNO'])){
      $result1_ms['TFM'][] = $item['SUBSID'];
    }else{
      $result1_ms['KBRO'][] = $item['SUBSID'];
    }
  }
  foreach($result1_ms as $db => $subsid_arr){
    $dbh = null;
    switch ($db) {
      case 'CG':
        $dbh = GetDBH('CGCossMS');
        break;
      case 'TFM':
        $dbh = GetDBH('TFMCossMS');
        break;
      case 'KBRO':
        $dbh = GetDBH('kbroCossMS');
        break;  
    }
    $sql = "select companyno as ori_companyno,right(companyno,3) companyno,disctime,subsid,chargename from ms0210 with (nolock)
          where chargename like '%付費固定%' and subsid in ('".  implode("','", $subsid_arr)."')
    ";
    $sth = mssql_query($sql,$dbh);
    while($row = mssql_fetch_assoc($sth)){
      //timestamp 
      if($row['disctime']!=''){
        $row['disctime'] = strtotime($row['disctime']);
      }
      $result1_ms_0210[$row['companyno']][$row['subsid']][$row['chargename']] = $row;
    }
  }
  //確認全部的付費固定IP狀態-----e
  //$result1 = 比對兩個名單, 以震江(1)的名單為主, 沒在名單中的要做以下的事情
//  echo '<pre>';print_r($result1);
  foreach($result1 as $item){
    $subsid = $item['SUBSID'];
    $ip = $item['IP'];
    $chargename = $item['CHARGENAME'];
    $pay = $item['PAY'];
    $mac = $item['MAC'];
    $cnr_id = $item['CNR_ID'];
    $companyno = $item['COMPANYNO'];

    $result1_ms_0210_temp = $result1_ms_0210[$item['COMPANYNO']][$item['SUBSID']][$item['CHARGENAME']];
    if (preg_match("/^(DE|ST)-.*/i", $result1_ms_0210_temp['ori_companyno'])){
      if($result1_ms_0210_temp['disctime']<time()){
        //(1)確認ms0210中的companyno狀態, 若companyno like 'DE-___'　or companyno like 'ST-___' and disctime < getdate() 
        $command = 'delfixip';
        $sql_ins = "insert into cnr_queue(cnr_id,command,ip,cpemac,companyno,subsid)values('$cnr_id','$command','$ip','$mac','$companyno','$subsid')";
        //$sth_ins = oci_parse($nms, $sql_ins);
        //oci_execute($sth_ins);
        $sql_del = "delete from cnr_fixip_coss where subsid='$subsid' and companyno='$companyno' and chargename='$chargename'";
        //$sth_del = oci_parse($nms, $sql_del);
        //oci_execute($sth_del);
        echo $command.'/'.implode('/', $item).' -> '.$sql_ins.' -> '.$sql_del;echo "<br>\n";
      }else{
        //(2) 若companyno like 'DE-___'　or companyno like 'ST-___' and (disctime is null or disctime >= getdate())
        if($pay!='lock'){
          $command ='deactiveip';
          $sql_ins = "insert into cnr_queue(cnr_id,command,ip,cpemac,companyno,subsid)values('$cnr_id','$command','$ip','$mac','$companyno','$subsid')";
          //$sth_ins = oci_parse($nms, $sql_ins);
          //oci_execute($sth_ins);
          $sql_upt = "update cnr_fixip_coss set pay='$pay' where subsid ='$subsid' and companyno='$companyno' and chargename='$chargename'";
          //$sth_upt = oci_parse($nms, $sql_upt);
          //oci_execute($sth_upt);
          echo $command.'/'.implode('/', $item).' -> '.$sql_ins.' -> '.$sql_upt;echo "<br>\n";
        }
      }
    }
  }
  //$result2 = 比對兩個名單, 以震江(1)的名單為主, 有在名單中的要做以下的事情
  foreach($result2 as $item){
    $subsid = $item['SUBSID'];
    $ip = $item['IP'];
    $chargename = $item['CHARGENAME'];
    $pay = $item['PAY'];
    $mac = $item['MAC'];
    $cnr_id = $item['CNR_ID'];
    $companyno = $item['COMPANYNO'];
    $command = 'activeip';
    if($pay!='Y'){
      $sql_ins = "insert into cnr_queue(cnr_id,command,ip,cpemac,companyno,subsid) values('$cnr_id','$command','$ip','$mac','$companyno','$subsid')";
      $sth_ins = oci_parse($nms, $sql_ins);
      oci_execute($sth_ins);
      $sql_upt = "Update cnr_fixip_coss set pay='Y',updateuser='FIXIP_CRON' where subsid='$subsid' and companyno='$companyno' and chargename='$chargename'";
      $sth_upt = oci_parse($nms, $sql_upt);
      oci_execute($sth_upt);
      echo $command.'/'.implode('/', $item).' -> '.$sql_ins.' -> '.$sql_upt;echo "<br>\n";
      
    }
    
  }
  
  
  
  oci_close($nms);
  mssql_close($dbh);
  
  $now = date("Y-m-d H:i:s");
  echo "END: $now ";echo "<br>\n";

?>
