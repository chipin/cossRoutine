<?php
  /*
     裝機 / 維修 派工明細, 從震江撈取匯入外撥系統

     2018.03.08 移植至V2執行
  */
  include_once('common.inc.php');

  function get_mobile($tel_arr = array()) {
    $a = '';
    foreach ($tel_arr as $tel) {
      if (substr($tel, -6, 6) == '000000') continue;
      if (preg_match("/^09[0-9]{8}$/", $tel)) {
        $a = $tel;
        break;
      }
    }
    return $a;
  }


  // for test
  $test_data = array();
  $test_tel = array('0982123680','0922440658','0939092000','0983045670','0922443157','0939611704','0911852746','0983408916','0922447429','0935864096','0932298279');
  //$test_tel = array('0935864096');
  //


  echo 'Start Time: ' . date("Y-m-d H:i:s") . "\n\n";

  // 取得昨日日期
  $ss = localtime(time() - 86400, true);
  $ss['tm_year'] += 1900;
  $ss['tm_mon']  += 1;
  if ($ss['tm_mon'] < 10)  $ss['tm_mon']  = '0' . $ss['tm_mon'];
  if ($ss['tm_mday'] < 10) $ss['tm_mday'] = '0' . $ss['tm_mday'];

  $yesterday = $ss['tm_year'] . $ss['tm_mon'] . $ss['tm_mday'];

  echo "GetDate: $yesterday\n\n";

  // 維修 - 排除故障原因
  $catv_3_exclude = array(
    'A0201 計劃性光纜轉接',           'A0202 計劃性同軸轉接',           'A0205 計劃性放大器調整(PL=計畫中的)', 'A0206 計劃性網路升級',         'A0302 HFC頻寬容量不足',
    'A0401 工程維護其他問題',         'C0129 到修前去電聯絡又正常',     'D0304 伺服主機設定失當',              'E0701 其他無法分類之線路故障', 'E0702 其他無法分類之器材故障',
    'E0801 HFC架空不斷電系統UPS故障', 'E0802 HFC電源供應器保險絲燒毀',  'E0803 HFC電源供應器故障',             'E0904 DNS主機故障或滿載',      'E0907 未能在短時間內判斷或解決的頭端問題',
    'F0102 光纜意外事故',             'F0103 同軸意外事故',             'F0104 因颱風損壞光纖線路',            'F0106 供電戶停電',             'F0107 其他意外事故',
    'F0108 業者施工損壞500P3同軸',    'F0109 業者施工損壞RG11(7C)同軸', 'F0110 業者施工損壞RG6(5C)同軸',       'F0201 台電停電斷訊',           'F0202 其他單位施工配合遷移光纜',
    'F0203 其他單位施工配合遷移同軸'
  );

  $cm_3_exclude = array(
    'A0201 計劃性光纜轉接',           'A0202 計劃性同軸轉接',          'A0302 HFC頻寬容量不足',          'A0401 工程維護其他問題',        'C0129 到修前去電聯絡又正常',
    'E0701 其他無法分類之線路故障',   'E0702 其他無法分類之器材故障',  'E0801 HFC架空不斷電系統UPS故障', 'E0802 HFC電源供應器保險絲燒毀', 'E0907 未能在短時間內判斷或解決的頭端問題',
    'F0102 光纜意外事故',             'F0103 同軸意外事故',            'F0106 供電戶停電',               'F0107 其他意外事故',            'F0108 業者施工損壞500P3同軸',
    'F0109 業者施工損壞RG11(7C)同軸', 'F0110 業者施工損壞RG6(5C)同軸', 'F0201 台電停電斷訊',             'F0202 其他單位施工配合遷移光纜','F0203 其他單位施工配合遷移同軸'
  );

  $cm_3_exclude_A = array(
    '20331 Online-Wi-Fi無法上網', '20331 ONLINE-WI-FI無法上網'
  );

  $dtv_3_exclude = array(
    'A0401 工程維護其他問題'
  );

  $fttb_3_exclude = array(
    'A0401 工程維護其他問題', 'C0129 到修前去電聯絡又正常', 'E0701 其他無法分類之線路故障', 'E0907 未能在短時間內判斷或解決的頭端問題', 'F0102 光纜意外事故',
    'F0106 供電戶停電',       'F0107 其他意外事故',         'F0201 台電停電斷訊'
  );

  // 找出 2裝機 / 3維修 案件
  $have2  = array(); $have2C = array();
  $have3  = array(); $have3C = array();

  $dbhO = GetPDO('CNIS','COSS','die');
  $dbhC = GetPDO('TFMCossMS','','die');
  $dbhQ = GetPDO('CS','','die');

  $paper_id = array(); // 0:裝機 1:維修
  $sthQ = $dbhQ->query("select p_id,type,service,status from paper where status='1'");
  while ($rowQ = $sthQ->fetch(PDO::FETCH_ASSOC)) {
    $p_id = $rowQ['p_id'];
    $p_type = $rowQ['type'];
    $p_service = $rowQ['service'];

    $paper_id[$p_type][$p_service] = $p_id;
    if ($p_service == '2 CM') {
      $paper_id[$p_type]['5 FTTB'] = $p_id;
      $paper_id[$p_type]['7 EOC'] = $p_id;
    }
  }
  print_r($paper_id);

  $soname = array();
  $sthQ = $dbhQ->query("select so,name1 from so where mso='TFM'");
  while ($rowQ = $sthQ->fetch(PDO::FETCH_ASSOC)) {
    $p_so = $rowQ['so'];
    $p_name = $rowQ['name1'];

    $soname[$p_so] = $p_name;
  }
  print_r($soname);
  //exit;

  // 裝機 ----------------------------------------------------------------------------------------------------------------------------------------------------
  if (1 == 0) {
    $p_type = 0;
    $paper_str = '';
    $paper_arr = $paper_id[$p_type];
    $paper_arr = array_unique($paper_arr);
    if (count($paper_arr) > 0) {
      $paper_str = implode("','", $paper_arr);
      $paper_str = "'" . $paper_str . "'";
      echo 'paper_id: ' . $paper_str . "\n";
    }
    else
      die("ERROR: no install paper\n");

    $sqlC = "select
             C.CompanyNo,C.ServiceName,C.CustStatus,C.SubsID,C.SubsName,C.CustID,C.TeleNum01,C.TeleNum02,C.TeleNum03,C.CellPhone01,C.CellPhone02,C.CustSource,C.BrokerKind,C.CustBroker,C.PackageName,C.BillItem,C.SaleCampaign,C.SWVersion,C.SWVersion2,C.ChargeName2,
             B.WorkKind,A.WorkSheet,A.SheetStatus,convert(varchar,A.AcceptDate,120) AcceptDate,A.CreateName AcceptName,convert(varchar,A.BookDate,120) BookDate,convert(varchar,A.FinishTime,120) FinishTime,convert(varchar(10),A.FinishDate,120) FinishDate,convert(varchar,A.CleanDate,120) CleanDate,A.Worker1,A.Worker2,A.BackCause,A.BackCause1,
             case when len(E.EventItem) > 0 or len(E.EventDesc) > 0 then 1 else 0 end as pass,G.ChargeName ChargeName3
             from MS0301 A WITH (NOLOCK)
             inner join MS0300 B WITH (NOLOCK) on B.CompanyNo=A.CompanyNo and B.WorkSheet=A.WorkSheet
             inner join MS0200 C WITH (NOLOCK) on C.CompanyNo=A.CompanyNo and C.SubsID=A.SubsID
             left join MS0212 E WITH (NOLOCK) on E.CompanyNo=A.CompanyNo and E.SubsID=A.SubsID and ((E.EventItem like '%問卷外撥%' and E.EventItem like '%剔除%') or (E.EventDesc like '%問卷外撥%' and E.EventDesc like '%剔除%'))
             left join MS0301 G WITH (NOLOCK) on G.CompanyNo=A.CompanyNo and G.WorkSheet=A.WorkSheet and G.ServiceName=A.ServiceName and G.ChargeName like '%智慧錄影設備%' and G.SheetStatus not in ('A.取消','3.退單')
             where
             A.CompanyNo in ('101','103','104','300','701') and A.ServiceName in ('2 CM','5 FTTB','7 EOC','3 DSTB','C HS') and
             A.ChargeKind = '20' and B.WorkKind = '1 裝機' and
             ((A.FinishTime is not NULL and A.FinishTime != '') or (A.CleanDate is not NULL and A.CleanDate != '')) and
             A.SheetStatus not in ('A.取消','3.退單') and A.Worker1 != '' and A.Worker1 is not NULL and
             C.SubsName not like '%套房%' and B.MDUName not like '%學舍%' and C.CustCharacter not like '%滿意度外撥%' and
             cast(replace(convert(varchar(10),A.BookDate,111),'/','') as varchar(8)) = '$yesterday'
             order by
             case when a.servicename in ('1 CATV') then 5
                  when a.servicename in ('3 DSTB') then 4
                  when a.servicename in ('2 CM') then 3
                  when a.servicename in ('5 FTTB','7 EOC') then 2
                  when a.servicename in ('C HS') then 1
             else 9 end asc,C.CompanyNo,C.SubsID,A.CreateTime desc";
    echo '裝機: ' . $sqlC . "\n";
    $sthC = $dbhC->query($sqlC);
    while ($rowC = $sthC->fetch(PDO::FETCH_ASSOC)) {
      $so = $rowC['CompanyNo'];
      $custid = $rowC['CustID'];
      $subsid = $rowC['SubsID'];
      $servicename = $rowC['ServiceName'];
      $subsname = $rowC['SubsName'];
      $packagename = $rowC['PackageName'];
      $billitem = $rowC['BillItem'];
      $chargename2 = $rowC['ChargeName2'];
      $chargename3 = $rowC['ChargeName3'];
      $swversion = $rowC['SWVersion'];
      $brokerkind = $rowC['BrokerKind'];
      $worksheet = $rowC['WorkSheet'];
      $acceptname = $rowC['AcceptName'];
      $worker1 = $rowC['Worker1'];
      $finishtime = $rowC['FinishTime'];
      $backcause = $rowC['BackCause'];
      $backcause1 = $rowC['BackCause1'];
      $pass = $rowC['pass'];
      $tel1 = $rowC['TeleNum01'];
      $tel2 = $rowC['TeleNum02'];
      $tel3 = $rowC['TeleNum03'];
      $tel4 = $rowC['CellPhone01'];
      $tel5 = $rowC['CellPhone02'];
      $p_id = $paper_id[$p_type][$servicename];

      $chargename4 = '';
      if (!empty($chargename3))
        $chargename4 = $chargename3;
      else if (!empty($chargename2))
        $chargename4 = $chargename2;

      echo "$servicename,$so,$subsid,$tel1,$tel2,$tel3,$tel4,$tel5,$worksheet => ";

      if (empty($p_id)) {
        echo "no paper\n";
        continue;
      }

      $tel_arr = array($tel1,$tel2,$tel3,$tel4,$tel5);
      $mobile = get_mobile($tel_arr);
      if (empty($mobile)) {
        echo "no mobile\n";
        continue;
      }

      // 剔除件
      if ($pass == 1) {
        echo "rejection\n";
        continue;
      }

      // 過濾重覆客戶
      if ($have2[$subsid] == 1 || $have2C[$custid] == 1) {
        echo "duplication\n";
        continue;
      }

      $have2[$subsid]  = 1;
      $have2C[$custid] = 1;

      // 過濾掉七日內 相同住戶編號 外撥成功
      $sqlO1 = "select sid from custlist@TFM_ICARE_IVR where uptdate >= sysdate-7 and status='1' and flowtype in ('CATVBB','DSTB','HS') and accountnumber='$custid' order by sid desc";
      $sthO = $dbhO->query($sqlO1);
      $rowO = $sthO->fetch(PDO::FETCH_ASSOC);
      if ($rowO['SID'] > 0) {
        echo 'duplication 7days (ctidb) ' . $rowO['SID'] . "\n";
        echo "$sqlO1\n";
        continue;
      }

      // 過濾掉七日內 相同住戶編號 有回填者
      $sqlQ1 = "select cust_p_id from cust_quest_paper where createtime >= '2018-03-16' and answertime >= date_sub(now(), interval 7 day) and status='2' and p_id in ($paper_str) and custid='$custid' order by cust_p_id desc limit 1";
      $sthQ = $dbhQ->query($sqlQ1);
      $rowQ = $sthQ->fetch(PDO::FETCH_ASSOC);
      if ($rowQ['cust_p_id'] > 0) {
        echo 'duplication 7days (csdb) ' . $rowQ['cust_p_id'] . "\n";
        echo "$sqlQ1\n";
        continue;
      }

      $token = md5($so.','.$subsid.','.microtime(true).','.rand(100, 999));
      $code = '';
      while(1) {
        $cnt = 0;
        $code = substr(str_shuffle("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"), 0, 6);
        $sqlx = "select count(*) cnt from short_url where time >= date_sub(now(), interval 100 day) and token = '$code'";
        $sthQ = $dbhQ->query($sqlx);
        $rowQ = $sthQ->fetch(PDO::FETCH_ASSOC);
        $cnt = $rowQ['cnt'];
        if ($cnt == 0) {
          $orig_url = 'https://cs.digihome.com.tw/quest/satisfactionSurvey.php?token=' . $token;
          $sqlx = "insert into short_url (token,url,time) values ('$code','$orig_url',now())";
          $dbhQ->exec($sqlx);
          break;
        }
      }
      $url = 'cs.digihome.com.tw/?' . $code;

      $sms_mesg = '';
      if ($servicename == 'C HS')
        $sms_mesg = '您好，感謝您申辦台灣大寬頻居家防護服務，誠摯的邀請您抽空填寫裝機滿意度問卷 ' . $url;
      else if (in_array($servicename, array('2 CM','5 FTTB','7 EOC')))
        $sms_mesg = '您好，感謝您申辦台灣大寬頻光纖上網服務，誠摯的邀請您抽空填寫裝機滿意度問卷 ' . $url;
      else if (in_array($servicename, array('1 CATV','3 DSTB')))
        $sms_mesg = '您好，感謝您申辦' . $soname[$so] . '數位電視服務，誠摯的邀請您抽空填寫裝機滿意度問卷 ' . $url;
      if (empty($sms_mesg)) {
        echo "no sms_mesg\n";
        continue;
      }


      // for test
      /*
      $mobile = '';
      foreach ($test_tel as $tt) {
        if (!isset($test_data[$tt][$servicename])) {
          $mobile = $tt;
          $test_data[$tt][$servicename] = 1;
          break;
        }
      }
      if (empty($mobile)) {
        echo "no test mobile $url\n";
        continue;
      }
      */
      // for test


      // deadline = date_add(now(), interval 7 day)
      $sqlQ2 = "insert into cust_quest_paper (so,subsid,p_id,createtime,deadline,url,token,custid,servicename,subsname,mobile,packagename,billitem,brokerkind,swversion,chargename2,worksheet,acceptname,worker1,finishtime,backcause,backcause1)
                values ('$so','$subsid','$p_id',now(),'2018-04-02 23:59:59','$url','$token','$custid','$servicename','$subsname','$mobile','$packagename','$billitem','$brokerkind','$swversion','$chargename4','$worksheet','$acceptname','$worker1','$finishtime','$backcause','$backcause1')";
      $dbhQ->exec($sqlQ2);
      $cust_p_id = $dbhQ->lastInsertId();

      // SMS
      $sqlO2 = "insert into oss_sms (sys,sender,target,msg,so,subsid) values ('TFMICARE','quest','$mobile','$sms_mesg','$so','$subsid')";
      $dbhO->exec($sqlO2);

      echo "OK $cust_p_id\n";
      echo "$sqlO1\n$sqlQ1\n$sqlQ2\n$sqlO2\n";
    }

    echo "\n";
  }

  print_r($test_data);


  // 維修 ----------------------------------------------------------------------------------------------------------------------------------------------------
  if (1 == 0) {
    $p_type = 1;
    $paper_str = '';
    $paper_arr = $paper_id[$p_type];
    $paper_arr = array_unique($paper_arr);
    if (count($paper_arr) > 0) {
      $paper_str = implode("','", $paper_arr);
      $paper_str = "'" . $paper_str . "'";
      echo 'paper_id: ' . $paper_str . "\n";
    }
    else
      die("ERROR: no repair paper\n");

    $sqlC = "select
             C.CompanyNo,C.ServiceName,C.CustStatus,C.SubsID,C.SubsName,C.CustID,C.TeleNum01,C.TeleNum02,C.TeleNum03,C.CellPhone01,C.CellPhone02,C.CustSource,C.BrokerKind,C.CustBroker,C.PackageName,C.BillItem,C.SaleCampaign,C.SWVersion,C.SWVersion2,C.ChargeName2,
             B.WorkKind,A.WorkSheet,A.SheetStatus,convert(varchar,A.AcceptDate,120) AcceptDate,A.CreateName AcceptName,convert(varchar,A.BookDate,120) BookDate,convert(varchar,A.FinishTime,120) FinishTime,convert(varchar(10),A.FinishDate,120) FinishDate,convert(varchar,A.CleanDate,120) CleanDate,A.Worker1,A.Worker2,A.BackCause,A.BackCause1,
             B.WorkCause,
             CASE when A.SheetStatus in ('4.結款','4 結案') then
               CASE
                 when A.BackCause1 != '' and A.BackCause1 is not NULL then A.BackCause1
                 when A.CleanCause != '' and A.CleanCause is not NULL then A.CleanCause
                 when A.BackCause != '' and A.BackCause is not NULL then A.BackCause else '' END
             else '' END as BackCause2,
             case when len(E.EventItem) > 0 or len(E.EventDesc) > 0 then 1 else 0 end as pass
             from MS0301 A WITH (NOLOCK)
             inner join MS0300 B WITH (NOLOCK) on A.CompanyNo=B.CompanyNo and A.WorkSheet=B.WorkSheet
             inner join MS0200 C WITH (NOLOCK) on A.CompanyNo=C.CompanyNo and A.SubsID=C.SubsID
             left join MS0212 E WITH (NOLOCK) on E.CompanyNo=A.CompanyNo and E.SubsID=A.SubsID and ((E.EventItem like '%問卷外撥%' and E.EventItem like '%剔除%') or (E.EventDesc like '%問卷外撥%' and E.EventDesc like '%剔除%'))
             where
             A.CompanyNo in ('101','103','104','300','701') and A.ServiceName in ('1 CATV','2 CM','5 FTTB','7 EOC','3 DSTB') and
             B.WorkKind = '5 維修' and A.SheetStatus not in ('A.取消','3.退單') and A.Worker1 != '' and A.Worker1 is not NULL and
             cast(replace(convert(varchar(10),A.BookDate,111),'/','') as varchar(8)) = '$yesterday'
             order by
             case when a.servicename in ('2 CM','5 FTTB','7 EOC') and c.billitem like '%連線費%' then
                    case when isnumeric(substring(c.billitem,charindex('連線費',c.billitem)+3,charindex('M/',c.billitem)-charindex('連線費',c.billitem)-3)) = 0 then 1
                         when substring(c.billitem,charindex('連線費',c.billitem)+3,charindex('M/',c.billitem)-charindex('連線費',c.billitem)-3) < 60 then 1
                    else 5 end
                  when a.servicename in ('3 DSTB') and c.packagename not like '%DTA%' and c.billitem not like '%DTA%' then 2
                  when a.servicename in ('3 DSTB') then 3
                  when a.servicename in ('2 CM','5 FTTB','7 EOC') then 4
             else 9 end asc,C.CompanyNo,C.SubsID,A.CreateTime desc";
    echo '維修: ' . $sqlC . "\n";
    $sthC = $dbhC->query($sqlC);
    while ($rowC = $sthC->fetch(PDO::FETCH_ASSOC)) {
      $so = $rowC['CompanyNo'];
      $custid = $rowC['CustID'];
      $subsid = $rowC['SubsID'];
      $servicename = $rowC['ServiceName'];
      $subsname = $rowC['SubsName'];
      $packagename = $rowC['PackageName'];
      $billitem = $rowC['BillItem'];
      $chargename2 = $rowC['ChargeName2'];
      $swversion = $rowC['SWVersion'];
      $brokerkind = $rowC['BrokerKind'];
      $worksheet = $rowC['WorkSheet'];
      $acceptname = $rowC['AcceptName'];
      $worker1 = $rowC['Worker1'];
      $finishtime = $rowC['FinishTime'];
      $backcause = $rowC['BackCause'];
      $backcause1 = $rowC['BackCause1'];
      $backcause2 = $rowC['BackCause2'];
      $workcause = $rowC['WorkCause'];
      $pass = $rowC['pass'];
      $tel1 = $rowC['TeleNum01'];
      $tel2 = $rowC['TeleNum02'];
      $tel3 = $rowC['TeleNum03'];
      $tel4 = $rowC['CellPhone01'];
      $tel5 = $rowC['CellPhone02'];
      $p_id = $paper_id[$p_type][$servicename];

      echo "$servicename,$so,$subsid,$tel1,$tel2,$tel3,$tel4,$tel5,$backcause,$workcause,$backcause2 => ";

      $tel_arr = array($tel1,$tel2,$tel3,$tel4,$tel5);
      $mobile = get_mobile($tel_arr);
      if (empty($mobile)) {
        echo "no mobile\n";
        continue;
      }

      // 剔除件
      if ($pass == 1) {
        echo 'rejection' . "\n";
        continue;
      }

      // 排除故障原因
      $exclude = 0;
      if ($servicename == '1 CATV') {
        while (list($kkk, $vvv) = each($catv_3_exclude)) {
          if (trim($vvv) == trim($backcause2)) {
            $exclude = 1;
            break;
          }
        }
        reset($catv_3_exclude);
      }
      else if ($servicename == '2 CM') {
        while (list($kkk, $vvv) = each($cm_3_exclude)) {
          if (trim($vvv) == trim($backcause2)) {
            $exclude = 1;
            break;
          }
        }
        reset($cm_3_exclude);
      }
      else if ($servicename == '3 DSTB') {
        while (list($kkk, $vvv) = each($dtv_3_exclude)) {
          if (trim($vvv) == trim($backcause2)) {
            $exclude = 1;
            break;
          }
        }
        reset($dtv_3_exclude);
      }
      else if ($servicename == '5 FTTB' || $servicename == '7 EOC') {
        while (list($kkk, $vvv) = each($fttb_3_exclude)) {
          if (trim($vvv) == trim($backcause2)) {
            $exclude = 1;
            break;
          }
        }
        reset($fttb_3_exclude);
      }

      if ($exclude == 1) {
        echo ' → Exclude BackCause' . "\n";
        continue;
      }

      // 排除派工原因
      $exclude = 0;
      if ($servicename == '2 CM') {
        while (list($kkk, $vvv) = each($cm_3_exclude_A)) {
          if (trim($vvv) == trim($workcause)) {
            $exclude = 1;
            break;
          }
        }
        reset($cm_3_exclude_A);
      }

      if ($exclude == 1) {
        echo ' → Exclude WorkCause' . "\n";
        continue;
      }

      // 過濾重覆客戶
      if ($have3[$subsid] == 1 || $have3C[$custid] == 1) {
        echo ' → Duplication' . "\n";
        continue;
      }

      $have3[$subsid]  = 1;
      $have3C[$custid] = 1;

      /*
      // 過濾掉七日內 相同住戶編號 外撥成功
      $sqlO = "select sid from custlist@TFM_ICARE_IVR where uptdate >= sysdate-7 and status='1' and flowtype in ('REPAIR') and accountnumber='$custid' order by sid desc";
      $sthO = $dbhO->query($sqlO);
      $rowO = $sthO->fetch(PDO::FETCH_ASSOC);

      if ($rowO['SID'] > 0) {
        echo ' → Duplication 7days (ctidb) ' . $rowO['SID'] . "\n";
        continue;
      }
      */

      echo " → OK $sid\n";
      //echo "→ $sqlO\n$sqlO1\n$sqlO2\n$sqlO3\n";
    }
  }

  echo "\n" . 'Stop Time: ' . date("Y-m-d H:i:s") . "\n";
?>
