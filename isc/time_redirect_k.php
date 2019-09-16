<?php
  /*
    請使用UTF-8 without BOM編碼
    Written by Karen 2014.6.9
  */
  //include_once('smarty.inc.php');
  include_once('common.inc.php');
  //session_start();


  $dbh_event = GetDBH('KBRO_NMSDB','EVENT');
  $dbh_coss = GetDBH('KBRO_NMSDB','COSS');
  //$cnis = GetDBH('TFM_NMSDB','CNIS');
  $dbh = GetDBH('CNIS');
  //$dbh_isc = GetDBH('ISC_M');

  $kbro_coss = GetDBH('kbroCossMS');
  $cg_coss = GetDBH('CGCossMS');

  $cnt = 0;
  while($cnt<3){
    $dbh_isc = GetDBH('ISC_M','isc','getError');
    if (preg_match("/^Error/", $dbh_isc,$tmp)){
      $cnt += 1;
    }else{
      break;
    }
    echo $dbh_isc."<br>\n";
  }

  if (is_string($dbh_isc)) {
    if (stristr($dbh_isc, 'error')) {
      echo "ERROR: Unable to connect to ISCDB";
      exit;
    }
  }

  var_dump($tmp);

  /*if ($cnt > 0){
    $sql = "insert into sms_queue_pay@tfnnms(external,mbl_nbr,msg,ins_date,account)
            values('585655','0939758773','ISC mysql連線失敗',sysdate,'KARENCHIU')";
    $sth = oci_parse($cnis,$sql);
    oci_execute($sth);
  }*/

  $now = date("Y-m-d H:i:s");
  echo "START: $now\n";

  # 現在時間 + 600秒, 來取得設定時間及日期
  $time = date('Y/m/d H:i:s',mktime(date('H'), date('i'), date('s')+600, date('m'), date('d'), date('Y')));
  echo 'Now + 600sec ='.$time."<br>\n";

  $week = date("w",mktime(date('H'), date('i'), date('s')+600, date('m'), date('d'), date('Y')));

  $hour = date("H",mktime(date('H'), date('i'), date('s')+600, date('m'), date('d'), date('Y')));

  if ($week == '0')
    $week = 7;
  echo 'hour:'.$hour."<br>\n";

  $hr_v = 'h'.((int)$hour+1);
  $iscAry = array();

  $sql = "select companyno,isc from so";
  $sth = oci_parse($dbh,$sql);
  oci_execute($sth);
  while($row = oci_fetch_assoc($sth)){

    if ($row['ISC'] == 'allot'){
      $table = 'custdata_allot';
    }elseif ($row['ISC'] == 'procera'){
      $table = 'custdata_procera';
    }
    $iscAry[$row['COMPANYNO']] = $table;

  }

  // LOCK
  $sql = "mysql lock table custdata_procera write, custdata_allot write";
  echo "$sql\n";
  //mysql_query($sql, $dbh_isc);

  ##更新時段設定
  $cm_time_ary = array();
  $hr_ary = array('N','Y');
  $i = 0;
  $cnt = 0;
  foreach($hr_ary as $hr_status){
	  $qsql = "select trim(a.soid) soid,a.subsid, $hr_v hrs from cm_set a, cm_time b where a.subsid=b.subsid and a.cmset='B' and b.weekday='$week' and a.stopyn='N' and $hr_v = '$hr_status' ";
	  echo $qsql."<br>\n";
	  $sth = oci_parse($dbh_event,$qsql);
	  oci_execute($sth);
	  while($row = oci_fetch_assoc($sth)){
	  	  $cnt +=1;
	      $companyno = $row['SOID'];
	      $subsid = $row['SUBSID'];
	      $block = $row['HRS'];
	      
	      $cm_time_ary[$hr_status][$companyno][] = $subsid;
	     
				$upt = "";
				
	      
	      
	      $upd_sql2 = "insert into cm_time_seting_log(soid,subsid,func,updatetime) values('$companyno','$subsid','$block_flag',sysdate)";
	      //$uptsth = oci_parse($dbh_event,$upd_sql2);
	      //oci_execute($uptsth);
	
	      if (!empty($iscAry[$companyno])){
	        $qry = "select * from $iscAry[$companyno] where companyno='$companyno' and subsid='$subsid'";
	        $qrysth = @mysql_query($qry,$dbh_isc);
	        if($qryrow = mysql_fetch_assoc($qrysth)){
	          $upt = "update $iscAry[$companyno] set timeblock='$block_flag',updatetime=sysdate() where companyno='$companyno' and subsid='$subsid'";
	
	        }else{
	          $upt = "insert into $iscAry[$companyno] (companyno,subsid,timeblock) values('$companyno','$subsid','$block_flag')";
	
	        }
	
	        //print 'b-upt:'.$upt."<br>\n";
	
	
	        //@mysql_query($upt,$dbh_isc);
	
	      }
	      //print 'B-cm_status:'.$companyno.':'.$subsid.':'.$block_flag.';B-isc:'.$companyno.':'.$subsid.':'.$block_flag."<br>\n";
	
	  }
	}
  
  
 //echo implode("'",$cm_time_ary['Y']['101']);
  foreach($cm_time_ary as $type =>$so){
    foreach($so as $companyno=>$subsid){
    		echo $type.":".$companyno.":".implode("'",$cm_time_ary[$type][$companyno])."<br>\n";
    }
   
  }
  
  

  
  // UNLOCK
  $sql = "mysql unlock tables";
  echo "$sql\n";
  //mysql_query($sql, $dbh_isc);

  oci_close($dbh_event);
  oci_close($dbh_coss);
  oci_close($dbh);
  mysql_close($dbh_isc);
  mssql_close($kbro_coss);

  $now = date("Y-m-d H:i:s");
  echo "END: $now\n\n";
?>
