<?php
  /*
     Written by Yen-Chih Yu(Swallow) 2015.01.07

     裝機 / 維修 派工明細, 從震江DB撈取匯入問卷DB, 並過濾條件.
  */
  include_once('/usr/local/apache/htdocs/questionary/include/getdb.inc');

  function filtertel ($so = '', $tel = '') {
    if ($tel == '0900000000')
      $tel = '';
    else if (preg_match("/^09[0-9]{8}$/", $tel)) {
    }
    else if (preg_match("/^[1-9]{1}[0-9]{6,7}$/", $tel)) {
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
  $now_sec = time(); // 現在秒數

  // 取得昨日日期
  $ss = localtime(time() - 86400, true);
  $ss['tm_year'] += 1900;
  $ss['tm_mon']  += 1;
  if ($ss['tm_mon'] < 10)  $ss['tm_mon']  = '0' . $ss['tm_mon'];
  if ($ss['tm_mday'] < 10) $ss['tm_mday'] = '0' . $ss['tm_mday'];

  $yesterday = $ss['tm_year'] . $ss['tm_mon'] . $ss['tm_mday'];

  echo "GetDate: $yesterday\n\n";

  // 維修問卷 - 排除故障原因
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

  $cm_3_exclude_A = array('20331 Online-Wi-Fi無法上網','20331 ONLINE-WI-FI無法上網');

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

  $dbhC = GetDBH('CossMS');
  $dbhL = GetDBH('CSD');
  $dbhO = GetDBH('iCare:ldbdba');

  // 裝機 ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
  $sqlC = "select
           C.CompanyNo as 系統代碼,D.AliasName as 系統名稱,B.WorkKind as 工務類別,A.ServiceName as 服務別,
           C.CustStatus as 訂戶狀態,C.SubsID as 訂戶編號,C.SubsName as 訂戶名稱,C.CustID as 住戶編號,
           isnull(C.TeleNum01,'') as 聯絡電話一,isnull(C.TeleNum02,'') as 聯絡電話二,isnull(C.TeleNum03,'') as 聯絡電話三,isnull(C.CellPhone01,'') as 聯絡電話四,isnull(C.CellPhone02,'') as 聯絡電話五,
           convert(varchar(10),C.TieStart,120) as 綁約開始,convert(varchar(10),C.TieDate,120) as 綁約截止,
           F.MSCITY as 縣市,F.MSDISTRICT as 鄉鎮市,F.MSDISTRICT+F.ADDRNAME as 裝機地址,
           CASE when F.NodeNo = '未設' then '' else isnull(F.NodeNo,'') END as 投落點,isnull(F.MDUName,'') as 大樓名稱,
           B.CustSource as 進件通路一,B.BrokerKind as 進件通路二,B.CustBroker as 進件通路三,
           isnull(B.SaleCampaign,'') as 業務活動,
           convert(varchar,A.AcceptDate,120) as 受理時間,A.CreateName as 受理人員,convert(varchar,A.BookDate,120) as 預約時間,substring(convert(varchar,A.FinishDate,120),1,10) as 完工日期,
           CASE when B.MSComment1 != '' and B.MSComment1 is not NULL and A.MSRemark != '' and A.MSRemark is not NULL and B.MSComment1 != A.MSRemark then cast(B.MSComment1+char(13)+char(10)+A.MSRemark as varchar(255))
              when B.MSComment1 != '' and B.MSComment1 is not NULL and A.MSRemark != '' and A.MSRemark is not NULL and B.MSComment1 = A.MSRemark then cast(B.MSComment1 as varchar(255))
              when B.MSComment1 != '' and B.MSComment1 is not NULL and (A.MSRemark = '' or A.MSRemark is null) then cast(B.MSComment1 as varchar(255))
              when (B.MSComment1 = '' or B.MSComment1 is null) and A.MSRemark != '' and A.MSRemark is not NULL then cast(A.MSRemark as varchar(255))
           else '' END as 備註,
           CASE when A.ServiceName != '1 CATV' then A.PackageName else '' END as 套餐,A.ChargeName as 收費項目,
           A.Worker1 as 工程人員一,A.Worker2 as 工程人員二,A.WorkSheet as 工單單號,A.SheetStatus as 工單狀態,A.CreateTime as 工單時間,
           CASE when len(E.EventItem) > 0 then rtrim(ltrim(E.EventItem))
              when len(E.EventDesc) > 0 then rtrim(ltrim(E.EventDesc))
           else '' END as 剔除,G.ChargeName chargename2
           from MS0301 as A WITH (INDEX(PK_MS0301), NOLOCK)
           inner join MS0300 as B WITH (INDEX(PK_MS0300), NOLOCK) on B.CompanyNo=A.CompanyNo and B.WorkSheet=A.WorkSheet
           inner join MS0200 as C WITH (INDEX(PK_MS0200), NOLOCK) on C.CompanyNo=A.CompanyNo and C.SubsID=A.SubsID
           inner join CDCompany as D WITH (INDEX(PK_CDCompany), NOLOCK) on D.CompanyNo=A.CompanyNo
           inner join MS0102 as F WITH (INDEX(PK_MS0102), NOLOCK) on F.CustID=C.CustID and F.AddrNo='0'
           left join MS0212 as E WITH (INDEX(PK_MS0212), NOLOCK) on E.CompanyNo=A.CompanyNo and E.SubsID=A.SubsID and (rtrim(ltrim(E.EventItem)) in ('問卷外撥-剔除件') or rtrim(ltrim(E.EventDesc)) in ('問卷外撥-剔除件'))
           left join MS0301 as G WITH (NOLOCK) on G.CompanyNo=A.CompanyNo and G.WorkSheet=A.WorkSheet and G.ServiceName='3 DSTB' and G.ChargeName like '%智慧錄影設備%' and G.SheetStatus not in ('A.取消','3.退單')
           where
           A.CompanyNo in ('101','103','104','300','701') and A.ServiceName in ('1 CATV','2 CM','5 FTTB','7 EOC','3 DSTB','C HS') and
           A.ChargeKind = '20' and ((A.FinishTime is not NULL and A.FinishTime != '') or (A.CleanDate is not NULL and A.CleanDate != '')) and
           B.WorkKind in ('1 裝機') and cast(replace(convert(varchar(10),A.BookDate,111),'/','') as varchar(8)) = '$yesterday'
           and A.SheetStatus not in ('A.取消','3.退單')
           and A.Worker1 != '' and A.Worker1 is not NULL
           and C.SubsName not like '%套房%'
	   and B.MDUName not like '%學舍%'
	   and C.CustCharacter not like '%滿意度外撥%'
           order by
	   case when a.servicename in ('1 CATV') then 5
                when a.servicename in ('3 DSTB') then 4 
                when a.servicename in ('2 CM') then 3 
                when a.servicename in ('5 FTTB') then 2 
		when a.servicename in ('C HS') then 1
           else 9 end asc,C.CompanyNo,C.SubsID,A.CreateTime desc";
  echo $sqlC . "\n";
  $sthC = $dbhC->query($sqlC);
  while ($rowC = $sthC->fetch(PDO::FETCH_ASSOC)) {
    $companyno = $rowC['系統代碼'];
    $custid = $rowC['住戶編號'];
    $subsid = $rowC['訂戶編號'];
    $servicename = $rowC['服務別'];
    $subsname = $rowC['訂戶名稱'];
    $subsname = $rowC['訂戶名稱'];
    $chargename2 = $rowC['chargename2'];
    if (empty($chargename2)) $chargename2 = 'X';

    $tel = array();
    $tel1 = $rowC['聯絡電話一'];
    $tel2 = $rowC['聯絡電話二'];
    $tel3 = $rowC['聯絡電話三'];
    $tel4 = $rowC['聯絡電話四'];
    $tel5 = $rowC['聯絡電話五'];

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

    echo "裝機: $companyno,$servicename,$custid,$subsid,$subsname,$tel_str,$chargename2";

    // 剔除件
    if (trim($rowC['剔除']) == '問卷外撥-剔除件') {
      echo ' → Rejection' . "\n";
      continue;
    }

    // 過濾重覆客戶
    if ($have2[$subsid] == 1 || $have2C[$custid] == 1) {
      echo ' → Duplication' . "\n";
      continue;
    }

    // 過濾掉七日內 相同住戶編號 2願意受訪-本人, 3願意受訪-非本人, 5拒訪
    $sqlL = "select count(A.cust_paper_id) as count
             from cust_question_paper as A
             inner join question_paper as B on B.paper_id=A.paper_id
             inner join CustomerCoss as C on C.SubsID=A.cust_id
             where B.type >= 1 and B.type <= 4 and A.status in ('2','3','5') and A.end_time >= from_unixtime(unix_timestamp(now())-(86400*7)) and C.CustID='$custid'";
    $sthL = $dbhL->query($sqlL);
    $rowL = $sthL->fetch(PDO::FETCH_ASSOC);

    if ($rowL['count'] > 0) {
      $have2[$subsid]  = 1;
      $have2C[$custid] = 1;
      echo ' → Duplication 7days (mysql)' . "\n";
      continue;
    }

    $have2[$subsid]  = 1;
    $have2C[$custid] = 1;

    // 過濾掉七日內 相同住戶編號 外撥成功
    $sqlO = "select sid from custlist
             where status='1' and flowtype in ('CATVBB','DSTB','HS') and uptdate >= sysdate-7 and accountnumber='$custid' order by sid desc";
    $sthO = $dbhO->query($sqlO);
    $rowO = $sthO->fetch(PDO::FETCH_ASSOC);

    if ($rowO['SID'] > 0) {
      $have2[$subsid]  = 1;
      $have2C[$custid] = 1;
      echo ' → Duplication 7days (oracle)' . "\n";
      continue;
    }

    $have2[$subsid]  = 1;
    $have2C[$custid] = 1;

    while (list($k1, $v1) = each($rowC)) { // 編碼轉換, 特殊字元處理
      $v1 = trim($v1);
      $v1 = htmlspecialchars($v1, ENT_QUOTES);
      $v1 = stripslashes($v1);

      $rowC[$k1] = $v1;
    }
    reset($rowC);

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

    $sid = 0;
    $sqlO1 = "insert into custlist (customer_id,name,accountnumber,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$subsid','$subsname','$custid','$tel_str','0','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename') returning sid into :sid";
    $sthO = $dbhO->prepare($sqlO1);
    $sthO->bindParam(':sid', $sid, PDO::PARAM_INT, 32);
    $sthO->execute();

    if (!empty($sid)) {
      $sqlO2 = "insert into currentnamelist (sid,customer_id,name,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$sid','$subsid','$subsname','$tel_str','S','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename')";
      $dbhO->exec($sqlO2);
    }

    echo " → OK $sid\n";
    echo "$sqlO1\n$sqlO2\n";

/*
    // 查詢贈品
    $gift = '';
    $sthC2 = $dbhC->query("select ChargeName,MStatus from MS3820 WITH (INDEX(IX_MS38201), NOLOCK) where GiftCNo='" . $rowC['系統代碼'] . "' and SubsID='" . $rowC['訂戶編號'] . "' and RecvNo='" . $rowC['工單單號'] . "'");
    while ($rowC2 = $sthC2->fetch(PDO::FETCH_ASSOC)) {
      $gift .= (!empty($gift) ? ',' : '' ) . $rowC2['ChargeName'] . ' <' . $rowC2['MStatus'] . '>';
    }

    if (!empty($rowC['備註'])) $rowC['備註'] = '【裝機' . $rowC['工單單號'] . "】\n" . $rowC['備註'];

    $sthL = $dbhL->query("select * from CustomerCoss where SO='" . $rowC['系統名稱'] . "' and SubsID='" . $rowC['訂戶編號'] . "'");
    $rowL = $sthL->fetch(PDO::FETCH_ASSOC);

    if (!empty($rowL['SubsID'])) {
      if ($rowC['訂戶狀態'] == '6 裝機中' && empty($rowC['收費項目'])) $rowC['收費項目'] = $rowL['BillChargeName'];

      $sqlL = "update CustomerCoss set
               ServiceName='" . $rowC['服務別'] . "', CustID='" . $rowC['住戶編號'] . "', CustStatus='" . $rowC['訂戶狀態'] . "', SubsName='" . $rowC['訂戶名稱'] . "',
               TeleNum01='" . $rowC['聯絡電話一'] . "', TeleNum02='" . $rowC['聯絡電話二'] . "', TeleNum03='" . $rowC['聯絡電話三'] . "', CellPhone01='" . $rowC['聯絡電話四'] . "', CellPhone02='" . $rowC['聯絡電話五'] . "',
               City='" . $rowC['縣市'] . "', District='" . $rowC['鄉鎮市'] . "', InstAddrName='" . $rowC['裝機地址'] . "', MDUName='" . $rowC['大樓名稱'] . "', NodeNo='" . $rowC['投落點'] . "',
               BillSaleCampaign='" . $rowC['業務活動'] . "', BillPackageName='" . $rowC['套餐'] . "', BillChargeName='" . $rowC['收費項目'] . "',
               BillTieStart='" . $rowC['綁約開始'] . "', BillTieEnd='" . $rowC['綁約截止'] . "'
               where SO='" . $rowC['系統名稱'] . "' and SubsID='" . $rowC['訂戶編號'] . "'";
    }
    else {
      $sqlL = "insert into CustomerCoss set
               ServiceName='" . $rowC['服務別'] . "', CustID='" . $rowC['住戶編號'] . "', CustStatus='" . $rowC['訂戶狀態'] . "', SubsName='" . $rowC['訂戶名稱'] . "',
               TeleNum01='" . $rowC['聯絡電話一'] . "', TeleNum02='" . $rowC['聯絡電話二'] . "', TeleNum03='" . $rowC['聯絡電話三'] . "', CellPhone01='" . $rowC['聯絡電話四'] . "', CellPhone02='" . $rowC['聯絡電話五'] . "',
               City='" . $rowC['縣市'] . "', District='" . $rowC['鄉鎮市'] . "', InstAddrName='" . $rowC['裝機地址'] . "', MDUName='" . $rowC['大樓名稱'] . "', NodeNo='" . $rowC['投落點'] . "',
               BillSaleCampaign='" . $rowC['業務活動'] . "', BillPackageName='" . $rowC['套餐'] . "', BillChargeName='" . $rowC['收費項目'] . "',
               BillTieStart='" . $rowC['綁約開始'] . "', BillTieEnd='" . $rowC['綁約截止'] . "',
               RejectCall='N', SO='" . $rowC['系統名稱'] . "', SubsID='" . $rowC['訂戶編號'] . "'";
    }
    $dbhL->exec($sqlL);

    if (!empty($rowL['SubsID']) && $rowL['RejectCall'] == 'Y') { // 拒訪名單
      echo ' → RejectCall' . "\n";
      continue;
    }

    $sqlL = "insert into cust_question_paper set cust_id='" . $rowC['訂戶編號'] . "', paper_id='$paper_id2', import_time=from_unixtime($now_sec)";
    $dbhL->exec($sqlL);

    $lastid = $dbhL->lastInsertId(); // 取得 auto-increment 的號碼

    if (!empty($lastid)) {
      $sqlL = "insert into cust_question_paper_customer set cust_paper_id='$lastid',
               CustSource='" . $rowC['進件通路一'] . "', BrokerKind='" . $rowC['進件通路二'] . "', CustBroker='" . $rowC['進件通路三'] . "',
               SaleCampaign='" . $rowC['業務活動'] . "', PackageName='" . $rowC['套餐'] . "', ChargeName='" . $rowC['收費項目'] . "',
               Accepter='" . $rowC['受理人員'] . "', AcceptTime='" . $rowC['受理時間'] . "', BookTime='" . $rowC['預約時間'] . "', FinishDate='" . $rowC['完工日期'] . "',
               Worker1='" . $rowC['工程人員一'] . "', Worker2='" . $rowC['工程人員二'] . "', Comment='" . $rowC['備註'] . "', Gift='$gift'";
      $dbhL->exec($sqlL);
    }
*/
  }

  // 維修 ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
  $sqlC = "select
           C.CompanyNo as 系統代碼,D.AliasName as 系統名稱,B.WorkKind as 工務類別,A.ServiceName as 服務別,
           C.CustStatus as 訂戶狀態,C.SubsID as 訂戶編號,C.SubsName as 訂戶名稱,C.CustID as 住戶編號,
           isnull(C.TeleNum01,'') as 聯絡電話一,isnull(C.TeleNum02,'') as 聯絡電話二,isnull(C.TeleNum03,'') as 聯絡電話三,isnull(C.CellPhone01,'') as 聯絡電話四,isnull(C.CellPhone02,'') as 聯絡電話五,
           isnull(C.SaleCampaign,'') as 業務活動,isnull(C.PackageName,'') as 套餐,isnull(C.BillItem,'') as 收費項目,
           convert(varchar(10),C.TieStart,120) as 綁約開始,convert(varchar(10),C.TieDate,120) as 綁約截止,
           F.MSCITY as 縣市,F.MSDISTRICT as 鄉鎮市,F.MSDISTRICT+F.ADDRNAME as 裝機地址,
           CASE when F.NodeNo = '未設' then '' else isnull(F.NodeNo,'') END as 投落點,isnull(F.MDUName,'') as 大樓名稱,
           convert(varchar,A.AcceptDate,120) as 受理時間,A.CreateName as 受理人員,convert(varchar,A.BookDate,120) as 預約時間,substring(convert(varchar,A.FinishDate,120),1,10) as 完工日期,
           B.WorkCause as 派工原因,
           CASE when A.SheetStatus in ('4.結款','4 結案') then
             CASE
               when A.BackCause1 != '' and A.BackCause1 is not NULL then A.BackCause1
               when A.CleanCause != '' and A.CleanCause is not NULL then A.CleanCause
               when A.BackCause != '' and A.BackCause is not NULL then A.BackCause else '' END
           else '' END as 故障原因,
           CASE when B.MSComment1 != '' and B.MSComment1 is not NULL and A.MSRemark != '' and A.MSRemark is not NULL and B.MSComment1 != A.MSRemark then cast(B.MSComment1+char(13)+char(10)+A.MSRemark as varchar(255))
                when B.MSComment1 != '' and B.MSComment1 is not NULL and A.MSRemark != '' and A.MSRemark is not NULL and B.MSComment1 = A.MSRemark then cast(B.MSComment1 as varchar(255))
                when B.MSComment1 != '' and B.MSComment1 is not NULL and (A.MSRemark = '' or A.MSRemark is null) then cast(B.MSComment1 as varchar(255))
                when (B.MSComment1 = '' or B.MSComment1 is null) and A.MSRemark != '' and A.MSRemark is not NULL then cast(A.MSRemark as varchar(255))
           else '' END as 備註,
           A.Worker1 as 工程人員一,A.Worker2 as 工程人員二,A.WorkSheet as 工單單號,A.SheetStatus as 工單狀態,A.CreateTime as 工單時間,
           CASE when len(E.EventItem) > 0 then rtrim(ltrim(E.EventItem))
              when len(E.EventDesc) > 0 then rtrim(ltrim(E.EventDesc))
           else '' END as 剔除
           from MS0301 as A WITH (INDEX(PK_MS0301), NOLOCK)
           inner join MS0300 as B WITH (INDEX(PK_MS0300), NOLOCK) on A.CompanyNo=B.CompanyNo and A.WorkSheet=B.WorkSheet
           inner join MS0200 as C WITH (INDEX(PK_MS0200), NOLOCK) on A.CompanyNo=C.CompanyNo and A.SubsID=C.SubsID
           inner join CDCompany as D WITH (INDEX(PK_CDCompany), NOLOCK) on D.CompanyNo=A.CompanyNo
           inner join MS0102 as F WITH (INDEX(PK_MS0102), NOLOCK) on F.CustID=C.CustID and F.AddrNo='0'
           left join MS0212 as E WITH (INDEX(PK_MS0212), NOLOCK) on E.CompanyNo=A.CompanyNo and E.SubsID=A.SubsID and (rtrim(ltrim(E.EventItem)) in ('問卷外撥-剔除件') or rtrim(ltrim(E.EventDesc)) in ('問卷外撥-剔除件'))
           where
           A.CompanyNo in ('101','103','104','300','701') and A.ServiceName in ('1 CATV','2 CM','5 FTTB','7 EOC','3 DSTB') and
           B.WorkKind = '5 維修' and cast(replace(convert(varchar(10),A.BookDate,111),'/','') as varchar(8)) = '$yesterday'
           and A.SheetStatus not in ('A.取消','3.退單')
           and A.Worker1 != '' and A.Worker1 is not NULL
           order by
           case when a.servicename in ('2 CM','5 FTTB','7 EOC') and c.billitem like '%連線費%' then case when substring(c.billitem,charindex('連線費',c.billitem)+3,charindex('M/',c.billitem)-charindex('連線費',c.billitem)-3) < 60 then 1 else 5 end
                when a.servicename in ('3 DSTB') and c.packagename not like '%DTA%' and c.billitem not like '%DTA%' then 2
                when a.servicename in ('3 DSTB') then 3
                when a.servicename in ('2 CM','5 FTTB','7 EOC') then 4
           else 9 end asc,C.CompanyNo,C.SubsID,A.CreateTime desc";
  echo $sqlC . "\n";
  $sthC = $dbhC->query($sqlC);
  while ($rowC = $sthC->fetch(PDO::FETCH_ASSOC)) {
    $companyno = $rowC['系統代碼'];
    $custid = $rowC['住戶編號'];
    $subsid = $rowC['訂戶編號'];
    $servicename = $rowC['服務別'];
    $subsname = $rowC['訂戶名稱'];

    $tel = array();
    $tel1 = $rowC['聯絡電話一'];
    $tel2 = $rowC['聯絡電話二'];
    $tel3 = $rowC['聯絡電話三'];
    $tel4 = $rowC['聯絡電話四'];
    $tel5 = $rowC['聯絡電話五'];

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

    echo "維修: $companyno,$servicename,$custid,$subsid,$subsname,$tel_str";

    // 剔除件
    if (trim($rowC['剔除']) == '問卷外撥-剔除件') {
      echo ' → Rejection' . "\n";
      continue;
    }

    // 排除故障原因
    $exclude = 0;
    if ($rowC['服務別'] == '1 CATV') {
      while (list($kkk, $vvv) = each($catv_3_exclude)) {
        if (trim($vvv) == trim($rowC['故障原因'])) {
          $exclude = 1;
          break;
        }
      }
      reset($catv_3_exclude);
    }
    else if ($rowC['服務別'] == '2 CM') {
      while (list($kkk, $vvv) = each($cm_3_exclude)) {
        if (trim($vvv) == trim($rowC['故障原因'])) {
          $exclude = 1;
          break;
        }
      }
      reset($cm_3_exclude);
    }
    else if ($rowC['服務別'] == '3 DSTB') {
      while (list($kkk, $vvv) = each($dtv_3_exclude)) {
        if (trim($vvv) == trim($rowC['故障原因'])) {
          $exclude = 1;
          break;
        }
      }
      reset($dtv_3_exclude);
    }
    else if ($rowC['服務別'] == '5 FTTB' || $rowC['服務別'] == '7 EOC') {
      while (list($kkk, $vvv) = each($fttb_3_exclude)) {
        if (trim($vvv) == trim($rowC['故障原因'])) {
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
    if ($rowC['服務別'] == '2 CM') {
      while (list($kkk, $vvv) = each($cm_3_exclude_A)) {
        if (trim($vvv) == trim($rowC['派工原因'])) {
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

    // 過濾掉七日內 相同住戶編號 2願意受訪-本人, 3願意受訪-非本人, 5拒訪
    $sqlL = "select count(A.cust_paper_id) as count
             from cust_question_paper as A
             inner join question_paper as B on B.paper_id=A.paper_id
             inner join CustomerCoss as C on C.SubsID=A.cust_id
             where B.type >= 1 and B.type <= 4 and A.status in ('2','3','5') and A.end_time >= from_unixtime(unix_timestamp(now())-(86400*7)) and C.CustID='$custid'";
    $sthL = $dbhL->query($sqlL);
    $rowL = $sthL->fetch(PDO::FETCH_ASSOC);

    if ($rowL['count'] > 0) {
      $have3[$subsid]  = 1;
      $have3C[$custid] = 1;
      echo ' → Duplication 7days' . "\n";
      continue;
    }

    $have3[$subsid]  = 1;
    $have3C[$custid] = 1;

    // 過濾掉七日內 相同住戶編號 外撥成功
    $sqlO = "select sid from custlist
             where status='1' and flowtype in ('REPAIR') and uptdate >= sysdate-7 and accountnumber='$custid' order by sid desc";
    $sthO = $dbhO->query($sqlO);
    $rowO = $sthO->fetch(PDO::FETCH_ASSOC);

    if ($rowO['SID'] > 0) {
      $have3[$subsid]  = 1;
      $have3C[$custid] = 1;
      echo ' → Duplication 7days' . "\n";
      continue;
    }

    $have3[$subsid]  = 1;
    $have3C[$custid] = 1;

    while (list($k1, $v1) = each($rowC)) { // 編碼轉換, 特殊字元處理
      $v1 = trim($v1);
      $v1 = htmlspecialchars($v1, ENT_QUOTES);
      $v1 = stripslashes($v1);

      $rowC[$k1] = $v1;
    }
    reset($rowC);

    $flowtype = 'REPAIR';
    $flowid   = '003';
    $so_id    = '903';

    $sid = 0;
    $sqlO1 = "insert into custlist (customer_id,name,accountnumber,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$subsid','$subsname','$custid','$tel_str','0','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename') returning sid into :sid";
    $sthO = $dbhO->prepare($sqlO1);
    $sthO->bindParam(':sid', $sid, PDO::PARAM_INT, 32);
    $sthO->execute();

    if (!empty($sid)) {
      $sqlO2 = "insert into currentnamelist (sid,customer_id,name,tel,status,flowtype,flowid,so_id,createdate,so_code,servicename) values ('$sid','$subsid','$subsname','$tel_str','S','$flowtype','$flowid','$so_id',sysdate,'$companyno','$servicename')";
      $dbhO->exec($sqlO2);
    }

    echo " → OK $sid\n";
    echo "$sqlO1\n$sqlO2\n";

/*
    if (!empty($rowC['備註'])) $rowC['備註'] = '【維修' . $rowC['工單單號'] . "】\n" . $rowC['備註'];

    $sthL = $dbhL->query("select * from CustomerCoss where SO='" . $rowC['系統名稱'] . "' and SubsID='" . $rowC['訂戶編號'] . "'");
    $rowL = $sthL->fetch(PDO::FETCH_ASSOC);

    if (!empty($rowL['SubsID'])) {
      if ($rowC['訂戶狀態'] == '6 裝機中' && empty($rowC['收費項目'])) $rowC['收費項目'] = $rowL['BillChargeName'];

      $sqlL = "update CustomerCoss set
               ServiceName='" . $rowC['服務別'] . "', CustID='" . $rowC['住戶編號'] . "', CustStatus='" . $rowC['訂戶狀態'] . "', SubsName='" . $rowC['訂戶名稱'] . "',
               TeleNum01='" . $rowC['聯絡電話一'] . "', TeleNum02='" . $rowC['聯絡電話二'] . "', TeleNum03='" . $rowC['聯絡電話三'] . "', CellPhone01='" . $rowC['聯絡電話四'] . "', CellPhone02='" . $rowC['聯絡電話五'] . "',
               City='" . $rowC['縣市'] . "', District='" . $rowC['鄉鎮市'] . "', InstAddrName='" . $rowC['裝機地址'] . "', MDUName='" . $rowC['大樓名稱'] . "', NodeNo='" . $rowC['投落點'] . "',
               BillSaleCampaign='" . $rowC['業務活動'] . "', BillPackageName='" . $rowC['套餐'] . "', BillChargeName='" . $rowC['收費項目'] . "',
               BillTieStart='" . $rowC['綁約開始'] . "', BillTieEnd='" . $rowC['綁約截止'] . "'
               where SO='" . $rowC['系統名稱'] . "' and SubsID='" . $rowC['訂戶編號'] . "'";
    }
    else {
      $sqlL = "insert into CustomerCoss set
               ServiceName='" . $rowC['服務別'] . "', CustID='" . $rowC['住戶編號'] . "', CustStatus='" . $rowC['訂戶狀態'] . "', SubsName='" . $rowC['訂戶名稱'] . "',
               TeleNum01='" . $rowC['聯絡電話一'] . "', TeleNum02='" . $rowC['聯絡電話二'] . "', TeleNum03='" . $rowC['聯絡電話三'] . "', CellPhone01='" . $rowC['聯絡電話四'] . "', CellPhone02='" . $rowC['聯絡電話五'] . "',
               City='" . $rowC['縣市'] . "', District='" . $rowC['鄉鎮市'] . "', InstAddrName='" . $rowC['裝機地址'] . "', MDUName='" . $rowC['大樓名稱'] . "', NodeNo='" . $rowC['投落點'] . "',
               BillSaleCampaign='" . $rowC['業務活動'] . "', BillPackageName='" . $rowC['套餐'] . "', BillChargeName='" . $rowC['收費項目'] . "',
               BillTieStart='" . $rowC['綁約開始'] . "', BillTieEnd='" . $rowC['綁約截止'] . "',
               RejectCall='N', SO='" . $rowC['系統名稱'] . "', SubsID='" . $rowC['訂戶編號'] . "'";
    }
    $dbhL->exec($sqlL);

    if (!empty($rowL['SubsID']) && $rowL['RejectCall'] == 'Y') { // 拒訪名單
      echo ' → RejectCall' . "\n";
      continue;
    }

    $sqlL = "insert into cust_question_paper set cust_id='" . $rowC['訂戶編號'] . "', paper_id='$paper_id3', import_time=from_unixtime($now_sec)";
    $dbhL->exec($sqlL);

    $lastid = $dbhL->lastInsertId(); // 取得 auto-increment 的號碼

    if (!empty($lastid)) {
      $sqlL = "insert into cust_question_paper_customer set cust_paper_id='$lastid',
               Accepter='" . $rowC['受理人員'] . "', AcceptTime='" . $rowC['受理時間'] . "', BookTime='" . $rowC['預約時間'] . "', FinishDate='" . $rowC['完工日期'] . "',
               WorkCause='" . $rowC['派工原因'] . "', BreakCause='" . $rowC['故障原因'] . "',
               Worker1='" . $rowC['工程人員一'] . "', Worker2='" . $rowC['工程人員二'] . "', Comment='" . $rowC['備註'] . "'";
      $dbhL->exec($sqlL);
    }
*/
  }

  echo "\n" . 'Stop Time: ' . date("Y-m-d H:i:s") . "\n";
?>
