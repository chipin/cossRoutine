<?php
  /*
select * from oss_sms
where create_date >= to_date('20180122','yyyymmdd')
and sys='CTI'
order by sid desc

CNSIDB
172.16.13.43
COSS
SERVICE_NAME = CNISP

NMSDB
172.16.13.40
COSS
SERVICE_NAME = NMSDBP.kbro.com.tw

  */

  include_once('common.inc.php');

  if (!isset($argv[1])) die("Usage: $argv[0] MSO\n");
  $mso = $argv[1];



  if ($mso == 'TFM') {
    $sys = 'TFMICARE';
    $ora = GetDBH('CNIS','COSS');
    $dbh = GetDBH('TFMCossMS');
  }
  else if ($mso == 'CG') {
    $sys = 'CTI';
    $ora = GetDBH('KBRO_NMSDB','COSS');
    $dbh = GetDBH('CossMS_CG');
  }
  else if ($mso == 'kbro') {
    $sys = 'CTI';
    $ora = GetDBH('KBRO_NMSDB','COSS');
    $dbh = GetDBH('kbroCossMS');
  }
  else
    die("Usage: $argv[0] MSO\n");


  // 撈用戶資料
  $sql = "select top 5 companyno,subsid,cellphone01 from ms0200 with (nolock)
          where companyno in ('101','103','104','300','701','210','220','230','240','250','260','106','310','330','410','420','610','810','820')
          and servicename='2 CM' and custstatus='1 正常'
          and companyno='220' and subsname like '%凱擘%' and cellphone01 is not null and cellphone01 != ''";
  $sth = mssql_query($sql, $dbh);
  while ($row = mssql_fetch_assoc($sth)) {
    $so = $row['companyno'];
    $subsid = $row['subsid'];
    $cellphone01 = $row['cellphone01'];

    echo "$so, $subsid, $cellphone01\n";

    // 發簡訊
    $sql2 = "insert into oss_sms (sys,sender,target,msg,so,subsid) values ('$sys','quest','$cellphone01','簡訊內容','$so','$subsid')";
    //$sth2 = oci_parse($ora, $sql2);
    //oci_execute($sth2);
  }



?>

