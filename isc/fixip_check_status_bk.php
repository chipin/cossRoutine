<?php
  /*
    請使用UTF-8 without BOM編碼
    Written by Karen 2015.9.30
  */
  //include_once('smarty.inc.php');
  include_once('common.inc.php');
  //session_start();
  
  function logf($s)
  {
    $logname="fixip_check_status";
    $outf = fopen('/ap/home/coss/log/'.$logname.'_'.date('Ym').'.log','at');
    $hostip = getenv("REMOTE_ADDR");
    $url = $_SERVER['QUERY_STRING'];
    fprintf($outf, "[%s,%s,%s]%s\n", date('Y/m/d H:i:s'), $hostip, $url, $s);
    fclose($outf);
  }

  $now = date("Y-m-d H:i:s");
  echo "START: $now\n";

  
  $measure_server = "";
  $subsid_ary = array();
  
  $nms = GetDBH('CNIS');
  
  if ($argv[1] == 'KBRO'){
    $sosql = "'210','220','230','240','250','260','310','330','410','420','610','810','820'";
    $dbh = GetDBH('kbroCossMS');
    $measure_server = 'nms@ntp-qos';
  }else if ($argv[1] == 'TFM'){
    $sosql = "'101','103','104','300','701'";
    $dbh = GetDBH('TFMCossMS');
    $measure_server = 'nms@tfm-qos';
  }else{
    $sosql = "'106'";
    $dbh = GetDBH('CGCossMS');
    $measure_server = 'nms@ntp-qos';
  }
  

  
  
  /**2.判斷是否有週期收費欠費停機用戶, 固定IP停止發放, 但鎖住
     3.判斷是否有BB服務欠費/停機, 固定IP停止發放, 但鎖住
     4.判斷是否有BB服務退租, 取消固定IP
  **/
  
  /*固定IP狀態不為正常的訂編*/
  $ms0210_ip = array();
  $sql = "select a.companyno,a.custid,a.subsid,b.chargename,b.so,b.mscomment fixip,a.singlesn from ms0200 a with (nolock)
          inner join (
          select right(companyno,3) companyno,companyno as so, subsid,chargename,mscomment from ms0210 with (nolock)
          where chargename like '%付費固定IP%' and
          (companyno like '______' and (disctime is not null or disctime < getdate())) 
          ) b on b.companyno=a.companyno and b.subsid=a.subsid
          where len(a.companyno)=3 and a.companyno in ($sosql) and  a.servicename in ('2 CM') order by b.chargename asc";
  $sth = mssql_query($sql,$dbh);
  while($row = mssql_fetch_assoc($sth)){
    $ms0210_ip[$row['subsid']]['companyno'] = $row['companyno'];
    $ms0210_ip[$row['subsid']]['chargename'] = $row['chargename'];
    $ms0210_ip[$row['subsid']]['fixip'] = $row['fixip'];
    $ms0210_ip[$row['subsid']]['singlesn'] = $row['singlesn'];
    $ms0210_ip[$row['subsid']]['so'] = $row['so'];
  }          
  
  echo "COSS FIXIP:".print_r($ms0210_ip)."<br>\n";
  
  
          
  $subsid_status = array();
  $sql = "select companyno,subsid,ip,mac,chargename,stopyn,pay from cnr_fixip_coss where pay is not null ";
  $sth = oci_parse($nms,$sql);
  oci_execute($sth);
  while($row = oci_fetch_assoc($sth)){
    $stopyn = $row['STOPYN'];
    $subsid = $row['SUBSID'];
    $chargename = $row['CHARGENAME'];
    $companyno = $row['COMPANYNO'];
    $pay = $row['PAY'];
    if ($stopyn == 'N'){
      $qry = "select subsid,companyno,disctime from ms0210 with(nolock) where subsid = '$subsid' and companyno='$companyno' and chargename='$chargename' and companyno in ($sosql)";
      $qrysth = mssql_query($qry,$dbh);
      if ($qryrow = mssql_fetch_assoc($qrysth)){
        if (preg_match("/^ST/i", $qryrow['companyno']))
      }
      
    }else{
    }
  }
  
  
   
  
  
  
  
  
  
  
  

  
  oci_close($nms);
  mssql_close($dbh);
  
  $now = date("Y-m-d H:i:s");
  echo "END: $now\n\n";
?>
