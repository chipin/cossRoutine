<?php
  /*
    請使用UTF-8 without BOM編碼
    Written by Karen 2014.6.9
  */
  //include_once('smarty.inc.php');
  include_once('common.inc.php');
  //session_start();
  include_once('official_web_db.inc.php');
  
  $now = date("Y-m-d H:i:s");
  echo "START: $now\n";

  
  //$wwwdbh = GetDBH('wwwkbro');
  $dbh_event = GetDBH('KBRO_NMSDB','EVENT');
  $dbh_coss = GetDBH('KBRO_NMSDB','COSS');
  $kbro_coss = GetDBH('kbroCossMS');
  $dbh_isc = GetDBH('ISC_M');
  $nms = GetDBH('CNIS');
  $total_ms0210 = array();
  $iscAry = array();

  
  /*if ($argv[1] == 'KBRO1'){
    $sosql = "'210'";
    $dbh = GetDBH('kbroCossMS');
  }else if ($argv[1] == 'KBRO2'){
  	$sosql = "'310','330','410'";
    $dbh = GetDBH('kbroCossMS');
  }else if ($argv[1] == 'KBRO3'){
  	$sosql = "'420','610','810','820'";
    $dbh = GetDBH('kbroCossMS');
  }else if ($argv[1] == 'TFM1'){
    $sosql = "'101','103'";
    $dbh = GetDBH('TFMCossMS');
  }else if ($argv[1] == 'TFM2'){
    $sosql = "'104','300','701'";
    $dbh = GetDBH('TFMCossMS');
  }else{
    $sosql = "'106'";
    $dbh = GetDBH('CGCossMS');
  }*/
  $sosql = $argv[1];
  if (preg_match("/^(101|103|104|300|701)$/i", $argv[1])){
  	$dbh = GetDBH('TFMCossMS');
  	
  }else if ($argv[1] == '106'){
  	$dbh = GetDBH('CGCossMS');
  	
  }else{
  	$dbh = GetDBH('kbroCossMS');
  	
  }

  $qry = "select a.companyno,a.custid,a.subsid from ms0200 a with (nolock)
          inner join (
          select right(companyno,3) companyno,subsid from ms0210 with (nolock)
          where chargename like '%上網時間%' and
          (  (companyno like '___' and (expiredate is null or expiredate>getdate())) or (companyno like 'DE-___' and disctime >= getdate())  )
          ) b on b.companyno=a.companyno and b.subsid=a.subsid
          where len(a.companyno)=3 and a.companyno in ($sosql) and  a.servicename in ('2 CM','5 FTTB','7 EOC') and substring(a.custstatus,1,1) in ('0','1','6','8','9','7','B')
          and a.subsid='8071658'";
  echo $qry;
  $sth = mssql_query($qry,$dbh);
  $cnt = 0;
  $idx = 0;
  while($row= mssql_fetch_assoc($sth)){
    $subsid = $row['subsid'];
    $total_ms0210[$subsid]['so'] = $row['companyno'];
    $total_ms0210[$subsid]['cid'] = $row['custid'];
    $total_ms0210[$subsid]['sid'] = $row['subsid'];
    $idx += 1;
  }

  echo "Total:".$idx." subscribers(MS0210)<br>\n";

  $qry2 = "select a.companyno,a.custid,a.subsid from ms0200 a with (nolock),ms0301 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid
           and a.companyno in ($sosql) and a.servicename in ('2 CM','5 FTTB','7 EOC') and substring(a.custstatus,1,1) in ('0','1','6','8','9','7','B') and
           b.chargename like '%上網時間%' and substring(b.sheetstatus, 1, 1) not in ('4', 'A') and a.subsid='8071658'";
  $sth2 = mssql_query($qry2,$dbh);

  $idx = 0;
  while($row= mssql_fetch_assoc($sth2)){
    $subsid = $row['subsid'];
    $total_ms0210[$subsid]['so'] = $row['companyno'];
    $total_ms0210[$subsid]['cid'] = $row['custid'];
    $total_ms0210[$subsid]['sid'] = $row['subsid'];
    $cnt += 1;
    $idx += 1;
  }

  echo "Total:".$idx." subscribers(ms0301)<br>\n";

  $qry3 = "select a.companyno,a.custid,a.subsid from ms0200 a with (nolock),ms3200 b with (nolock) where a.companyno=b.companyno and a.subsid=b.subsid
           and a.companyno in ($sosql) and a.servicename in ('2 CM','5 FTTB','7 EOC') and substring(a.custstatus,1,1) in ('0','1','6','8','9','7','B') and
           b.chargename like '%上網時間%' and recvyn='Y' and passyn = 'N' and billexpire>=getdate() and substring(realrecv,1,1)<>'Y' and a.subsid='8071658'
           group by a.companyno,a.custid,a.subsid";
  $sth3 = mssql_query($qry3,$dbh);
  $idx = 0;
  while($row= mssql_fetch_assoc($sth3)){
    $subsid = $row['subsid'];
    $total_ms0210[$subsid]['so'] = $row['companyno'];
    $total_ms0210[$subsid]['cid'] = $row['custid'];
    $total_ms0210[$subsid]['sid'] = $row['subsid'];
    $idx += 1;
    $cnt += 1;
  }
  
  echo "Total:".$idx." subscribers(ms3200)<br>\n";
  
  $qry4 = "select companyno,subsid from ms0217 with (nolock) where substring(probstatus,1,1) in ('0','1')  and probcharge like '%時間管理%' 
  				 and companyno in ($sosql)  and subsid='8071658'
           and probdate1 <= getdate() and probdate2 >= getdate() group by companyno,subsid";
  $sth4 = mssql_query($qry4,$dbh);
  $idx=0;
  while($row= mssql_fetch_assoc($sth4)){
    $subsid = $row['subsid'];
    $total_ms0210[$subsid]['so'] = $row['companyno'];
    $total_ms0210[$subsid]['sid'] = $row['subsid'];
    $idx += 1;
    $cnt += 1;
  }

  echo "Total:".$idx." subscribers(ms0217)<br>\n";
  

  $sql = "select companyno,isc from so";
  $sth = oci_parse($nms,$sql);
  oci_execute($sth);
  while($row = oci_fetch_assoc($sth)){
    if ($row['ISC'] == 'allot'){
      $table = 'custdata_allot';
    }elseif ($row['ISC'] == 'procera'){
      $table = 'custdata_procera';
    }
    $iscAry[$row['COMPANYNO']] = $table;
  }

  ##將已取消時間管理的客戶做解除
  $cmtime_flag = array();
  $idx = 0;
  
  $query_ary = array("soid"=>"$sosql");
  $dbc = new OFFICIAL_WEB_CMTIME;
  $dbc_result = json_decode($dbc->aws_official_web('selectAll',$query_ary),true);
  echo count($dbc_result);
  if($dbc_result['count']!='0'){
  	  
	  foreach($dbc_result as $item){
	  	$subsid = $cflag = $soid = "";
			$subsid = $item['subsid'];
			$cflag = $item['flag'];
			$soid  = $item['soid'];
		  
		  if (empty($total_ms0210[$subsid]) && $subsid != '9061284'){
		    if ($cflag == 'Y'){
				  $query_ary1 = array("Data" =>array(
					array(
					  "subsid" => "$subsid",
					  "soid" => "$soid",
					  "flag" => "N",   //系統台，EX:220
		
					),
				  ));	
				  //$dbc->aws_official_web('update',$query_ary1);
				  //echo '解除客戶:'.$subsid."<br>\n";
			  /*$upt = "update cmtime set flag='N' where subsid='$subsid' and soid='$soid'";
			  print $upt."<br>\n";
			  mssql_query($upt,$wwwdbh);*/
				//echo '解除客戶:'.$subsid."<br>\n";
		   }
		  }else{
		    $cmtime_flag[$subsid] = $cflag;
		    $idx += 1;
		  }
		}
  }
 

  echo "cmtime Total:".$idx." cmtime records\n";

  // LOCK
  $sql = "mysql lock table custdata_allot write";
  echo "$sql\n";
 // mysql_query($sql, $dbh_isc);

  $idx = 0;
  $cm_set = array();
  $qry = "select trim(subsid)subsid,trim(soid)soid,cmset,type,stopyn from cm_set where trim(soid) in ($sosql) and subsid='8071658'";
  $qrysth = oci_parse($dbh_event,$qry);
  oci_execute($qrysth);
  while($row = oci_fetch_assoc($qrysth)){
  	$subsid = $soid = $cmset = $type = $stopyn = "";
    $subsid = $row['SUBSID'];
    $soid   = $row['SOID'];
    $cmset  = $row['CMSET'];
    $type   = $row['TYPE'];
    $stopyn = $row['STOPYN'];
    $cm_set[$subsid] = $stopyn;
    if (empty($total_ms0210[$subsid])){
      //為避免重覆更新, 另外做判斷
      if ($stopyn == 'N'){
        $upt = "update cm_set set stopyn='Y' where subsid='$subsid' and soid = '$soid'";
        print $upt."<br>\n";
        //$uptsth = oci_parse($dbh_event,$upt);
        //oci_execute($uptsth);
        $cm_set[$subsid] = 'Y';
        $upt = "update $iscAry[$soid] set timeblock='N',updatetime=sysdate() where subsid='$subsid' and companyno='$soid' and timeblock='Y'";
        
       // @mysql_query($upt,$dbh_isc);
       // $upt_count = mysql_affected_rows();
        if ($upt_count > 1) print $upt."<br>\n";
      }
         
     
      
    }else{
      $cm_set[$subsid] = $stopyn;
      $cmset_flag[$subsid] = 'Y';
      $idx +=1;
      //print $subsid."<br>\n";
    }
  }

  echo "cm_set Total:".$idx." cmtime records\n";

  // UNLOCK
  $sql = "mysql unlock tables";
  echo "$sql\n";
  //mysql_query($sql, $dbh_isc);


  ##寫入或更新時間管理狀態
  foreach($total_ms0210 as $sid =>$i){
    $xflag = $cmtime_flag[$sid];
    try{
      if (empty($cmtime_flag[$sid])){
		  
		 /* 
        $ins = "insert into cmtime(soid,subsid,pass,flag) values('".$total_ms0210[$sid]['so']."','$sid',NULL,'Y')";
        print "<br>\n".$ins."<br>\n";
        $uptsth = mssql_query($ins,$wwwdbh);*/
				$query_ary1 = array("Data" =>
				  array(
					array(
					  "subsid" => "$sid",
					  "name" => "NULL",
					  "pass" => "NULL",
					  "flag" => "Y",
					  "soid" => $total_ms0210[$sid]['so'],  
					  "type" =>"NULL",
					  "mobile" => "NULL"
					),
				  )
				);
				//$dbc->aws_official_web('insert',$query_ary1);
				echo '新增客戶:'.$sid."<br>\n";
      }else{
        if ($xflag == 'N' or $xflag == ''){
          try{
            /*$uptsql = "update cmtime set flag='Y' where subsid='$sid' and soid='".$total_ms0210[$sid]['so']."'";
            print "<br>\n".$uptsql."<br>\n";
            $sth = mssql_query($uptsql,$wwwdbh);*/
						$query_ary1 = array("Data" =>
						  array(
							array(
							  "subsid" => "$sid",
							  "soid" => $total_ms0210[$sid]['so'],
							  "flag" => "Y",   //系統台，EX:220
							),
						  )
						);
						//$dbc->aws_official_web('update',$query_ary1);
						echo "更新用戶:".$sid."<br>\n";
			
          }catch(Exception $e){
            echo 'Caught exception: ',  $e->getMessage(), "\n";
          }
        }
      }

      if (empty($cmset_flag[$sid])){
        $ins2 = "insert into cm_set(subsid,soid,cmset,type,stopyn) values('$sid','".$total_ms0210[$sid]['so']."','I','Y','N')";
        print "<br>\n".$ins2."<br>\n";
        //$inssth = oci_parse($dbh_event,$ins2);
        //oci_execute($inssth);
      }else{
        //如果stopyn已是N, 不重覆更新
        if ($cm_set[$sid] != 'N'){
          $upt2 = "update cm_set set stopyn ='N' where subsid='$sid' and soid='".$total_ms0210[$sid]['so']."'";
          print "<br>\n".$upt2."<br>\n";
          //$uptsth = oci_parse($dbh_event,$upt2);
          //oci_execute($uptsth);
        }
      }



    }catch(Exception $e){
      echo 'Caught exception: ',  $e->getMessage(), "\n";
    }

  }


  oci_close($dbh_event);
  mssql_close($dbh);
  //mssql_close($wwwdbh);
  mssql_close($kbro_coss);
  mysql_close($dbh_isc);

  $now = date("Y-m-d H:i:s");
  echo "END: $now\n\n";
?>
