<?php
  /*
    請使用UTF-8 without BOM編碼
  */
  header('Content-type:text/html; charset=utf8');

  session_start();
  include_once('common.inc.php');




  function logf ($ss) {
    $tme       = date('Y/m/d H:i:s');
    $tym       = date('Ym');
    $hostip    = getenv("REMOTE_ADDR");
    $unique_id = getenv("UNIQUE_ID");
    $outf = fopen('/ap/home/coss/log/isc_' . $tym . '.log','a+');
    if (flock($outf, LOCK_EX)) { // do an exclusive lock
      fprintf($outf, "[%s,%s,%s] %s\n", $tme, $unique_id, $hostip, $ss);
      flock($outf, LOCK_UN); // release the lock
    }
    fclose($outf);
  }







  if(!in_array($_SERVER['REMOTE_ADDR'],$ip_allow)){
      err_msg('IP不在允許範圍內');
  }

  $kbro  = GetDBH('kbroCossMS');

  $cg  = GetDBH('CGCossMS');
  $nms = GetDBH('CNIS');
  $kbro_coss = GetDBH('kbroCossMS');
  $cg_coss = GetDBH('CGCossMS');
  $dbh_isc = GetDBH('ISC_M');
  $dbh_event = GetDBH('KBRO_NMSDB','EVENT');
  $soAry = array();
  $msg = '';
  $data = GetInput();

  $subsid = $data['subsid'];
  $companyno = $data['so'];
  $flag   = $data['flag'];


  if($subsid=='' or $flag == '' )
  {
    logf('未傳入正確參數-subsid:'.$subsid.'-flag:'.$flag);
    $msg = 'ERROR';
    exit;

  }

  $qry = "select companyno,subsid,servicename,custstatus,singlesn,packagename,billitem from ms0200 with(Nolock) where subsid='$subsid'";
  if ($companyno == '106')
    $qrysth = mssql_query($qry,$cg_coss);
  else
    $qrysth = mssql_query($qry,$kbro_coss);

  if($qryrow = mssql_fetch_assoc($qrysth)){
     $companyno = $qryrow['companyno'];
     $servicename = $qryrow['servicename'];
     $custstatus  = $qryrow['custstatus'];
     $singlesn    = $qryrow['singlesn'];
     $packagename = $qryrow['packagename'];
     $billitem    = $qryrow['billitem'];
     $swversion   = $qryrow['swversion'];
     $hv = 'N';
  }else{
     logf('此客戶編號對映不到SO');
     $msg = 'ERROR';
     exit;
  }


  $sql = "select companyno,isc from so ";
  $sth2 = oci_parse($nms,$sql);
  oci_execute($sth2);
  while($row2 = oci_fetch_assoc($sth2)){
    if ($row2['ISC'] == 'allot')
      $table = 'custdata_allot';
    else if ($row2['ISC'] == 'procera')
      $table = 'custdata_procera';

    $soAry[$row2['COMPANYNO']] = $table;
  }


  if (!empty($soAry[$companyno])){
    if ($flag == 'Y'){
      $block_flag = 'N';
    }else{
      $block_flag = 'Y';
    }

    $upt = "insert into $iscAry[$companyno] (companyno,subsid,servicename,custstatus,singlesn,billitem,hv,updatetime,wait4sync,timeblock,swversion) values
        ('$companyno','$subsid','$servicename','$custstatus','$singlesn','$billitem','$hv',now(),'Y','$block_flag','$swversion') on duplicate key
        update servicename=values(servicename),custstatus=values(custstatus),singlesn=values(singlesn),billitem=values(billitem),updatetime=values(updatetime),
        wait4sync=values(wait4sync),timeblock=values(timeblock),swversio=values(swversion)";

    @mysql_query($upt,$dbh_isc);


  }

  logf('Companyno: ' . $so . ', CMMAC: ' . $cmmac . ', Subsid: ' . $subsid .', URL:' .$url);





?>


