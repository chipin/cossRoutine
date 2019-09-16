<?php
  /*
     裝機 / 維修 派工明細, 從震江撈取匯入外撥系統

     2018.03.08 移植至V2執行
  */
  include_once('common.inc.php');

  function filtertel ($so = '', $tel = '') {
    if (substr($tel, -6, 6) == '000000')
      $tel = '';
    else if (preg_match("/^09[0-9]{8}$/", $tel)) { // 手機
    }
    else if (preg_match("/^0[1-9]{1}[0-9]{6,8}$/", $tel)) { // 8~10碼
    }
    else if (preg_match("/^[1-9]{1}[0-9]{5,7}$/", $tel)) { // 6~8碼
      if ($so == '300')
        $tel = '03' . $tel;
      else if ($so == '701')
        $tel = '07' . $tel;
      else
        $tel = '02' . $tel;
    }
    else
      $tel = '';

    return $tel;
  }

  echo 'Start Time: ' . date("Y-m-d H:i:s") . "\n\n";

  // 取得昨日日期
  $ss = localtime(time() - 86400, true);
  $ss['tm_year'] += 1900;
  $ss['tm_mon']  += 1;
  if ($ss['tm_mon'] < 10)  $ss['tm_mon']  = '0' . $ss['tm_mon'];
  if ($ss['tm_mday'] < 10) $ss['tm_mday'] = '0' . $ss['tm_mday'];

  $yesterday = $ss['tm_year'] . $ss['tm_mon'] . $ss['tm_mday'];
  
  $show_date = date("Ymd", time()-86400*3);
  $show_date_end = date("Ymd", time());

  echo "GetDate: $yesterday\n\n";
  echo "GetDate_3: $show_date - $show_date_end\n\n";

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

  $dbhC = GetPDO('TFMCossMS','','die');
  $dbhO = GetPDO('CNIS','CTI','die');


  // 裝機 ----------------------------------------------------------------------------------------------------------------------------------------------------
  if (1 == 1) { 
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
             cast(replace(convert(varchar(10),A.FinishTime,111),'/','') as varchar(8)) = '$show_date'
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
      $companyno = $rowC['CompanyNo'];
      $custid = $rowC['CustID'];
      $subsid = $rowC['SubsID'];
      $servicename = $rowC['ServiceName'];
      $subsname = $rowC['SubsName'];
      $chargename2 = $rowC['ChargeName2'];
      $chargename3 = $rowC['ChargeName3'];
      $chargename4 = 'X';
      if (!empty($chargename3))
        $chargename4 = $chargename3;
      else if (!empty($chargename2))
        $chargename4 = $chargename2;
      $pass = $rowC['pass'];

      $tel = array();
      $tel1 = $rowC['TeleNum01'];
      $tel2 = $rowC['TeleNum02'];
      $tel3 = $rowC['TeleNum03'];
      $tel4 = $rowC['CellPhone01'];
      $tel5 = $rowC['CellPhone02'];

      $t_tel = filtertel($companyno, $tel1);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel2);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel3);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel4);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel5);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $tel_str = implode(',', array_keys($tel));

      echo "$companyno,$servicename,$custid,$subsid,$subsname,$tel_str,$chargename4";

      // 剔除件
      if ($pass == 1) {
        echo ' → Rejection' . "\n";
        continue;
      }

      // 過濾重覆客戶
      if ($have2[$subsid] == 1 || $have2C[$custid] == 1) {
        echo ' → Duplication' . "\n";
        continue;
      }

      $have2[$subsid]  = 1;
      $have2C[$custid] = 1;

      // 過濾掉七日內 相同住戶編號 外撥成功
      $sqlO = "select sid from custlist@TFM_ICARE_IVR where uptdate >= sysdate-7 and status='1' and flowtype in ('CATVBB','DSTB','HS') and accountnumber='$custid' order by sid desc";
      $sthO = $dbhO->query($sqlO);
      $rowO = $sthO->fetch(PDO::FETCH_ASSOC);

      if ($rowO['SID'] > 0) {
        echo ' → Duplication 7days (ctidb) ' . $rowO['SID'] . "\n";
        continue;
      }

      /* 無用
      while (list($k1, $v1) = each($rowC)) { // 編碼轉換, 特殊字元處理
        $v1 = trim($v1);
        $v1 = htmlspecialchars($v1, ENT_QUOTES);
        $v1 = stripslashes($v1);

        $rowC[$k1] = $v1;
      }
      reset($rowC);
      */

      if ($servicename == '3 DSTB') {
        $flowtype = 'DSTB';
        $flowid   = '002';
        $so_id    = '902';
      }
      else if ($servicename == 'C HS'){
        $flowtype = 'HS';
        $flowid   = '005';
        $so_id    = '905';
      }
      else {
        $flowtype = 'CATVBB';
        $flowid   = '001';
        $so_id    = '901';
      }

      $sqlO1 = "insert into custlist@TFM_ICARE_IVR (customer_id,name,accountnumber,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$subsid','$subsname','$custid','$tel_str','0','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename')";
      $dbhO->exec($sqlO1);

      $sid = 0;
      $sqlO2 = "select sid from custlist@TFM_ICARE_IVR where createdate >= sysdate-10/1440 and status='0' and flowtype in ('CATVBB','DSTB','HS') and customer_id='$subsid' order by sid desc";
      $sthO2 = $dbhO->query($sqlO2);
      $rowO2 = $sthO2->fetch(PDO::FETCH_ASSOC);
      if ($rowO2['SID'] > 0) $sid = $rowO2['SID'];

      if (!empty($sid)) {
        $sqlO3 = "insert into currentnamelist@TFM_ICARE_IVR (sid,customer_id,name,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$sid','$subsid','$subsname','$tel_str','S','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename')";
        $dbhO->exec($sqlO3);
      }

      echo " → OK $sid\n";
      echo "→ $sqlO\n$sqlO1\n$sqlO2\n$sqlO3\n";
    }

    echo "\n";
  }

  // 維修 ----------------------------------------------------------------------------------------------------------------------------------------------------
  if (1 == 1) {
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
             cast(replace(convert(varchar(10),A.FinishTime,111),'/','') as varchar(8)) = '$yesterday'
             and A.backcause not in ('E 公共工程','G 區域障礙','I 客戶因素','K 取消(其它)')
             and A.backcause != ''
             and A.workcause not like '%ONLINE-WI-FI無法上網%' and a.workcause not like '%主動派工-訊號品質異常%'
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
      $companyno = $rowC['CompanyNo'];
      $custid = $rowC['CustID'];
      $subsid = $rowC['SubsID'];
      $servicename = $rowC['ServiceName'];
      $subsname = $rowC['SubsName'];
      $backcause = $rowC['BackCause2'];
      $workcause = $rowC['WorkCause'];
      $pass = $rowC['pass'];

      $tel = array();
      $tel1 = $rowC['TeleNum01'];
      $tel2 = $rowC['TeleNum02'];
      $tel3 = $rowC['TeleNum03'];
      $tel4 = $rowC['CellPhone01'];
      $tel5 = $rowC['CellPhone02'];

      $t_tel = filtertel($companyno, $tel1);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel2);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel3);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel4);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($companyno, $tel5);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $tel_str = implode(',', array_keys($tel));

      echo "$companyno,$servicename,$custid,$subsid,$subsname,$tel_str,$workcause,$backcause";

      // 剔除件
      if ($pass == 1) {
        echo ' → Rejection' . "\n";
        continue;
      }

      // 排除故障原因
      $exclude = 0;
      if ($servicename == '1 CATV') {
        while (list($kkk, $vvv) = each($catv_3_exclude)) {
          if (trim($vvv) == trim($backcause)) {
            $exclude = 1;
            break;
          }
        }
        reset($catv_3_exclude);
      }
      else if ($servicename == '2 CM') {
        while (list($kkk, $vvv) = each($cm_3_exclude)) {
          if (trim($vvv) == trim($backcause)) {
            $exclude = 1;
            break;
          }
        }
        reset($cm_3_exclude);
      }
      else if ($servicename == '3 DSTB') {
        while (list($kkk, $vvv) = each($dtv_3_exclude)) {
          if (trim($vvv) == trim($backcause)) {
            $exclude = 1;
            break;
          }
        }
        reset($dtv_3_exclude);
      }
      else if ($servicename == '5 FTTB' || $servicename == '7 EOC') {
        while (list($kkk, $vvv) = each($fttb_3_exclude)) {
          if (trim($vvv) == trim($backcause)) {
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

      // 過濾掉七日內 相同住戶編號 外撥成功
      $sqlO = "select sid from custlist@TFM_ICARE_IVR where uptdate >= sysdate-7 and status='1' and flowtype in ('REPAIR') and accountnumber='$custid' order by sid desc";
      $sthO = $dbhO->query($sqlO);
      $rowO = $sthO->fetch(PDO::FETCH_ASSOC);

      if ($rowO['SID'] > 0) {
        echo ' → Duplication 7days (ctidb) ' . $rowO['SID'] . "\n";
        continue;
      }

      /* 無用
      while (list($k1, $v1) = each($rowC)) { // 編碼轉換, 特殊字元處理
        $v1 = trim($v1);
        $v1 = htmlspecialchars($v1, ENT_QUOTES);
        $v1 = stripslashes($v1);

        $rowC[$k1] = $v1;
      }
      reset($rowC);
      */

      $flowtype = 'REPAIR';
      $flowid   = '003';
      $so_id    = '903';

      $sqlO1 = "insert into custlist@TFM_ICARE_IVR (customer_id,name,accountnumber,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$subsid','$subsname','$custid','$tel_str','0','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename')";
      $dbhO->exec($sqlO1);

      $sid = 0;
      $sqlO2 = "select sid from custlist@TFM_ICARE_IVR where createdate >= sysdate-10/1440 and status='0' and flowtype in ('REPAIR') and customer_id='$subsid' order by sid desc";
      $sthO2 = $dbhO->query($sqlO2);
      $rowO2 = $sthO2->fetch(PDO::FETCH_ASSOC);
      if ($rowO2['SID'] > 0) $sid = $rowO2['SID'];

      if (!empty($sid)) {
        $sqlO3 = "insert into currentnamelist@TFM_ICARE_IVR (sid,customer_id,name,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$sid','$subsid','$subsname','$tel_str','S','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename')";
        $dbhO->exec($sqlO3);
      }

      echo " → OK $sid\n";
      echo "→ $sqlO\n$sqlO1\n$sqlO2\n$sqlO3\n";
    }
  }

  echo "\n" . 'Stop Time: ' . date("Y-m-d H:i:s") . "\n";
?>
