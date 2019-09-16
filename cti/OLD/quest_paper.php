<?php
  include_once('common.inc.php');
  $hsdbh = GetDBH('CS');
  
  // 問卷id & mso &到期日
  $paper_id = 2;
  $mso = 'kbro';
  $deadline = '2018-03-01 23:59:59';
  
  // 撈用戶資料
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
    die("Usage: $mso MSO\n");

  $sql = "select top 15 companyno,subsid,cellphone01,servicename from ms0200 with (nolock)
          where companyno in ('101','103','104','300','701','210','220','230','240','250','260','106','310','330','410','420','610','810','820')
          and servicename='2 CM' 
          and custstatus='1 正常'
          and companyno='220' 
          and subsname like '%凱擘%' 
          and cellphone01 is not null 
          and cellphone01 != ''";
  $cust = mssql_query($sql, $dbh);
  
  while ($row = mssql_fetch_assoc($cust)){

    $so = $row['companyno'];
    $subsid = $row['subsid'];
    //$cellphone01 = $row['cellphone01'];
    $cellphone01 = '0932298279';
  
    $token = md5($so.$subsid.$paper_id);
    
    // 產生短網址
    $apiKey = 'AIzaSyAKpM0KegoNibvj32VmJouwa5uHZ0fmMJ8'; // kbroapp@gmail
    $long_url = 'https://cs.digihome.com.tw/quest/satisfactionSurvey.php?token='.$token;
    $postData = array('longUrl' => $long_url);
    $jsonData = json_encode($postData);
    $curlObj = curl_init();
    curl_setopt($curlObj, CURLOPT_URL, 'https://www.googleapis.com/urlshortener/v1/url?key='.$apiKey);
    curl_setopt($curlObj, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($curlObj, CURLOPT_SSL_VERIFYPEER, 0);
    curl_setopt($curlObj, CURLOPT_HEADER, 0);
    curl_setopt($curlObj, CURLOPT_HTTPHEADER, array('Content-type:application/json'));
    curl_setopt($curlObj, CURLOPT_POST, 1);
    curl_setopt($curlObj, CURLOPT_POSTFIELDS, $jsonData);
    $response = curl_exec($curlObj);
    curl_close($curlObj);
    //echo $long_url."\n";
    //var_dump($response);
    $response = json_decode($response);
    $short_url= str_replace("https://goo.gl/","",$response->id);
    
    
    // 發簡訊
    $msg = $response->id;
    $sql_insert = "insert into oss_sms (sys,sender,target,msg,so,subsid) values ('$sys','quest','$cellphone01','$msg','$so','$subsid')";
    $sth = oci_parse($ora, $sql_insert);
    oci_execute($sth);

    // insert至問卷
    $sql2_insert = "INSERT INTO cust_quest_paper (so, subsid, p_id, status, createtime, deadline, url, token)
                    VALUES ('".$so."', ".$subsid.", ".$paper_id.", 0, now(), '".$deadline."', '".$short_url."', '".$token."')";
    mysql_query($sql2_insert,$hsdbh);

  }
  

?>

