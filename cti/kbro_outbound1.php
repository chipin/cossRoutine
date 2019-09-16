<?php
  /*
    裝機 / 維修 派工明細, 從震江撈取匯入外撥系統
    2018.03.13 移植至V2執行

    10.123.12.15 [12/Mar/2018:05:15:01] /GW/cti2/get_welcome_worksheet.php
    10.123.12.15 [12/Mar/2018:05:45:01] /GW/cti2/get_welcome_worksheet.php?flag=Q
    10.123.12.15 [12/Mar/2018:09:00:04] /GW/cti2/get_yesterday_worksheet.php?status=1
    10.123.12.15 [12/Mar/2018:09:40:01] /GW/cti2/get_yesterday_worksheet.php?status=4
    10.123.12.15 [12/Mar/2018:13:30:02] /GW/cti2/get_yesterday_worksheet.php?status=2
    10.123.12.15 [12/Mar/2018:18:00:02] /GW/cti2/get_yesterday_worksheet.php?status=3

    status=1~3 僅發送簡訊, 通知用戶已完工
    get_yesterday_worksheet.php?status=5 2016/2暫停執行
    get_welcome_worksheet.php?flag=Q 有在呼叫, 但沒在用

    2018.07.01 正式啟用 BB<60M TV、DSTB、HS
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

  function filtertel ($so = '', $tel = '') {
    if (substr($tel, -6, 6) == '000000')
      $tel = '';
    else if (preg_match("/^09[0-9]{8}$/", $tel)) { // 手機
    }
    else if (preg_match("/^0[1-9]{1}[0-9]{6,8}$/", $tel)) { // 8~10碼
    }
    else if (preg_match("/^[1-9]{1}[0-9]{5,7}$/", $tel)) { // 6~8碼
      if (in_array($so, array('310','330')))
        $tel = '03' . $tel;
      else if (in_array($so, array('410','420')))
        $tel = '04' . $tel;
      else if ($so == '610')
        $tel = '06' . $tel;
      else if (in_array($so, array('810','820')))
        $tel = '08' . $tel;
      else
        $tel = '02' . $tel;
    }
    else
      $tel = '';

    return $tel;
  }

  // for test
  $test_data = array();
  //$test_tel = array('0935864096','0922447429');
  $test_tel = array('0922447429');
  // for test

  if (!isset($argv[1])) die("Usage: $argv[0] flag\n");
  $p_flag = $argv[1];
  //if (!in_array($p_flag, array('I','Q','1','2','3','4'))) die("Usage: $argv[0] flag\n");
  if (!in_array($p_flag, array('I'))) die("Usage: $argv[0] flag\n");

  if (date('Ymd') < '20180701') die("ERROR: today is not allowed to run");

  echo 'Start Time: ' . date("Y-m-d H:i:s") . "\n\n";

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
  $sthQ = $dbhQ->query("select so,name1 from so where mso='kbro'");
  while ($rowQ = $sthQ->fetch(PDO::FETCH_ASSOC)) {
    $p_so = $rowQ['so'];
    $p_name = $rowQ['name1'];

    $soname[$p_so] = $p_name;
  }
  print_r($soname);

  if (in_array($p_flag, array('1','2','3','4'))) $dbhO = GetPDO('KBRO_NMSDB','OEMS','die');
  $dbhS = GetPDO('KBRO_NMSDB','COSS','die');

  $cossdb = array('kbroCossMS','CGCossMS');
  //$cossdb = array('CGCossMS');
  foreach ($cossdb as $db) {
    echo "$db\n";

    $dbhC = GetPDO($db,'','return');
    if (is_string($dbhC) || empty($dbhC)) {
      echo "$dbhC\n\n";
      continue;
    }

    if ($db == 'CGCossMS')
      $so_str = "'106'";
    else
      $so_str = "'210','220','230','240','250','260','310','330','410','420','610','810','820'";

    $have = $haveC = $haveT = array();

    if ($p_flag == 'I') { // 裝機
      $show_date = date("Y/m/d", time()-86400*1);
      $show_date_end = date("Y/m/d", time());
      $p_type = 0;

      $sql = "select
              c.companyno,c.servicename,c.custstatus,c.subsid,c.subsname,c.custid,c.telenum01,c.telenum02,c.telenum03,c.cellphone01,c.cellphone02,c.custsource,c.brokerkind,c.custbroker,c.packagename,c.billitem,c.salecampaign,c.swversion,c.swversion2,c.chargename2,
              b.workkind,a.worksheet,a.sheetstatus,convert(varchar,a.acceptdate,120) acceptdate,a.createname acceptname,convert(varchar,a.bookdate,120) bookdate,convert(varchar,a.finishtime,120) finishtime,convert(varchar(10),a.finishdate,120) finishdate,convert(varchar,a.cleandate,120) cleandate,a.worker1,a.worker2,a.backcause,a.backcause1,
              g.chargename chargename3
              from ms0301 a with (nolock)
              inner join ms0300 b with (nolock) on b.companyno=a.companyno and b.worksheet=a.worksheet
              inner join ms0200 c with (nolock) on c.companyno=a.companyno and c.subsid=a.subsid
              left join ms0301 g with (nolock) on g.companyno=a.companyno and g.worksheet=a.worksheet and g.servicename=a.servicename and g.chargename like '%PVR設備%' and g.sheetstatus not in ('a.取消','3.退單')
              where
              c.companyno in ($so_str)
              and c.servicename in ('1 CATV','2 CM','3 DSTB','5 FTTB','7 EOC','C HS')
              and c.packagename not like '%子機%' and c.packagename not like '%DTA%'
              and c.custsource not like '%查緝%' and c.custsource not like '%緝私%'
              and c.brokerkind not like '%查緝%' and c.brokerkind not like '%緝私%' and c.brokerkind not like 'UTTNT%'
              and c.custkind01 not like '%九太%'
              and c.custcharacter not like '%NO CALL%'
              and b.workkind = '1 裝機'
              and a.chargekind = '20'
              and a.sheetstatus not in ('A.取消','3.退單')
              and a.finishtime between '$show_date' and '$show_date_end'
              order by
              case when a.servicename in ('1 CATV') then 5
                   when a.servicename in ('3 DSTB') then 4
                   when a.servicename in ('2 CM') then 3
                   when a.servicename in ('5 FTTB','7 EOC') then 2
                   when a.servicename in ('C HS') then 1
              else 9 end asc,c.companyno,c.custid,c.subsid,a.worksheet";
    }
    else if ($p_flag == 'Q') { // 高頻道
      continue;

      $show_date = date("Y/m/d", time()-86400*2);
      $show_date_end = date("Y/m/d", time()-86400*1);
      $sql =
      "
        select
          a.companyno,
          d.aliasname,
          b.custid,
          a.worksheet,
          a.servicename,
          (select top 1 1 from ms0210 with(nolock) where companyno = a.companyno and subsid = max(b.subsid) and chargename = '77082 聯網暨網路電視隨選服務') smod,
          max(b.subsid) subsid,
          max(b.subsname) subsname,
          max(b.telenum01) telenum01,
          max(b.cellphone01) cellphone01,
          max(b.telenum02) telenum02,
          max(b.cellphone02) cellphone02,
          max(b.telenum03) telenum03,
          convert(varchar(10),max(a.finishdate),111) finishdate,
          convert(varchar(19),max(a.finishtime),20) finishtime,
          convert(varchar(19),max(a.bookdate),20) bookdate,
          convert(varchar(19),max(a.acceptdate),20) acceptdate,
          max(c.mscity)+max(c.msdistrict) city,
          max(c.addrname) addrname,
          max(a.backcause) backcause,
          max(a.backcause1) backcause1,
          max(b.custcharacter) custcharacter,
          max(a.createname) createname,
          max(a.worker1) worker1,
          max(b.chargename2) chargename2,
          max(b.packagename) packagename
        from ms0300 am with (nolock), ms0301 a with (nolock), ms0200 b with (nolock), ms0102 c with (nolock), cdcompany d with (nolock)
        where
              a.companyno=b.companyno
          and a.subsid=b.subsid
          and a.companyno=d.companyno
          and a.companyno=am.companyno
          and a.worksheet=am.worksheet
          and a.companyno=c.companyno
          and a.custid=c.custid and c.addrno='0'
          and am.workkind in ('1 裝機')
          and am.custsource not like '%查緝%'
          and am.brokerkind not like '%查緝%' and am.brokerkind not like 'UTTNT%'
          and b.companyno in ($so_str)
          and b.servicename in ('2 CM','5 FTTB','7 EOC')
          and substring(b.custstatus,1,1) not in ('2','3','4','5','A')
          and b.custkind01 not like '%九太%'
          and b.custcharacter not like '%NO CALL%'
          and a.chargekind = '20'
          and a.sheetstatus not in ('A.取消','3.退單')
          and a.packagename not like '%試用%'
          and (a.packagename like '%60M%' or a.packagename like '%100M%' or a.packagename like '%120M%' or a.packagename like '%200M%' or a.packagename like '%300M%' or a.packagename like '%500M%' or a.packagename like '%800M%')
          and a.finishtime between '$show_date' and '$show_date_end'
        group by a.companyno,d.aliasname,b.custid,a.worksheet,a.servicename
        order by b.custid,
          case when a.servicename in ('C HS') then 1
          when a.servicename in ('5 FTTB','7 EOC') then 2
          when a.servicename in ('3 DSTB') then 4
          when a.servicename in ('2 CM') then 3
          when a.servicename in ('1 CATV') then 5
          end asc,a.companyno,a.worksheet
      ";
    }
    else if (in_array($p_flag, array('1','2','3','4','5'))) { // 維修
      continue;

      $Y_date = date("Y/m/d", time()-86400*1);
      $Z_date = date("Y/m/d", time()-86400*2);

      switch ($p_flag){
        case 1: // 昨天 18:00 ~ 今天 08:59
          $show_date_begin = $Y_date.' 18:00:00';
          $show_date_end = date("Y/m/d 08:59:59");
          $servicename_sql = "'1 CATV','2 CM','3 DSTB','5 FTTB','7 EOC','C HS'";
          $workcause_sql = "and a.workcause not like '%ONLINE-WI-FI無法上網%'";
          break;
        case 2: // 今天 09:00 ~ 今天 13:29
          $show_date_begin = date("Y/m/d 09:00:00");
          $show_date_end = date("Y/m/d 13:29:59");
          $servicename_sql = "'1 CATV','2 CM','3 DSTB','5 FTTB','7 EOC','C HS'";
          $workcause_sql = "and a.workcause not like '%ONLINE-WI-FI無法上網%'";
          break;
        case 3: // 今天 13:30 ~ 今天 17:59
          $show_date_begin = date("Y/m/d 13:30:00");
          $show_date_end = date("Y/m/d 17:59:59");
          $servicename_sql = "'1 CATV','2 CM','3 DSTB','5 FTTB','7 EOC','C HS'";
          $workcause_sql = "and a.workcause not like '%ONLINE-WI-FI無法上網%'";
          break;
        case 4: // 昨天 00:00 ~ 昨天 23:59
          $show_date_begin = $Y_date.' 00:00:00';
          $show_date_end = $Y_date.' 23:59:59';
          $servicename_sql = "'1 CATV','2 CM','3 DSTB','5 FTTB','7 EOC','C HS'";
          $workcause_sql = "and a.workcause not like '%ONLINE-WI-FI無法上網%'";
          break;
        case 5: // 前天 00:00 ~ 前天 23:59
          $show_date_begin = $Z_date.' 00:00:00';
          $show_date_end = $Z_date.' 23:59:59';
          $servicename_sql = "'1 CATV','2 CM','3 DSTB','5 FTTB','7 EOC'";
          $workcause_sql = "and a.workcause like '%ONLINE-WI-FI無法上網%'";
          break;
      }

      $sql =
      "
        select
          a.companyno,
          d.aliasname,
          b.custid,
          a.worksheet,
          a.servicename,
          max(b.subsid) subsid,
          max(b.subsname) subsname,
          max(b.telenum01) telenum01,
          max(b.cellphone01) cellphone01,
          max(b.telenum02) telenum02,
          max(b.cellphone02) cellphone02,
          max(b.telenum03) telenum03,
          convert(varchar(19),max(a.finishtime),121) finishdate,
          convert(varchar(19),max(a.finishtime),20) finishtime,
          convert(varchar(19),max(a.bookdate),20) bookdate,
          convert(varchar(19),max(a.acceptdate),20) acceptdate,
          max(c.mscity)+max(c.msdistrict) city,
          max(c.addrname) addrname,
          max(a.backcause) backcause,
          max(a.backcause1) backcause1,
          max(a.cleancause) cleancause,
          max(b.custcharacter) custcharacter,
          max(a.createname) createname,
          max(a.worker1) worker1,
          max(b.chargename2) chargename2,
          max(b.packagename) packagename,
          max(a.workcause) workcause,
          max(am.workteam) workteam
        from ms0300 am with (nolock),ms0301 a with (nolock), ms0200 b with (nolock), ms0102 c with (nolock), cdcompany d with (nolock)
        where
              a.companyno=b.companyno
          and a.subsid=b.subsid
          and a.companyno=d.companyno
          and a.companyno=am.companyno
          and a.worksheet=am.worksheet
          and a.companyno=c.companyno
          and a.custid=c.custid and c.addrno='0'
          and am.workkind='5 維修'
          and a.backcause not in ('K 取消(其它)')
          and a.sheetstatus not in ('A.取消','3.退單')
          and a.backcause not in ('E 公共工程','G 區域障礙','') and a.backcause is not null
          and b.companyno in ($so_str)
          and b.servicename in ($servicename_sql)
          and a.finishtime between '$show_date_begin' and '$show_date_end'
          $workcause_sql
          and b.custkind01 not like '%九太%'
          and b.custcharacter not like '%NO CALL%'
        group by a.companyno,d.aliasname,b.custid,a.worksheet,a.servicename
        order by
          case
          when a.servicename in ('C HS') then 1
          when a.servicename in ('5 FTTB') then 2
          when a.servicename in ('3 DSTB') then 4
          when a.servicename in ('2 CM') then 3
          when a.servicename in ('1 CATV') then 5
          end  asc,a.companyno,a.worksheet,b.custid
      ";
    }
    echo "$sql\n";
    $sthC = $dbhC->query($sql);
    while ($rowC = $sthC->fetch(PDO::FETCH_ASSOC)) {
      $so = $rowC['companyno'];
      $custid = $rowC['custid'];
      $subsid = $rowC['subsid'];
      $servicename = $rowC['servicename'];
      $subsname = $rowC['subsname'];
      $packagename = $rowC['packagename'];
      $billitem = $rowC['billitem'];
      $chargename2 = $rowC['chargename2'];
      $chargename3 = $rowC['chargename3'];
      $swversion = $rowC['swversion'];
      $brokerkind = $rowC['brokerkind'];
      $worksheet = $rowC['worksheet'];
      $acceptname = $rowC['acceptname'];
      $worker1 = $rowC['worker1'];
      $finishtime = $rowC['finishtime'];
      $backcause = $rowC['backcause'];
      $backcause1 = $rowC['backcause1'];
      $tel1 = $rowC['telenum01'];
      $tel2 = $rowC['telenum02'];
      $tel3 = $rowC['telenum03'];
      $tel4 = $rowC['cellphone01'];
      $tel5 = $rowC['cellphone02'];
      $p_id = $paper_id[$p_type][$servicename];

      $chargename4 = '';
      if (!empty($chargename3))
        $chargename4 = $chargename3;
      else if (!empty($chargename2))
        $chargename4 = $chargename2;

      echo "$servicename,$so,$subsid,$tel1,$tel2,$tel3,$tel4,$tel5,$worksheet => ";

      if (empty($p_id) || !isset($p_type)) {
        echo "no paper\n";
        continue;
      }

      // add by swallow 2018.04.26 保留BB<60M及其他
      if ($p_flag == 'I' && in_array($servicename, array('2 CM','5 FTTB','7 EOC'))) {
        if (preg_match("/(\d+)M\/\d+/i", $billitem, $mat)) {
          $bb = $mat[1];
          if ($bb >= 60) {
            echo "high BB\n";
            continue;
          }
        }
      }

      /*
      $tel = array();
      $t_tel = filtertel($so, $tel1);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($so, $tel2);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($so, $tel3);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($so, $tel4);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $t_tel = filtertel($so, $tel5);
      if (!empty($t_tel)) $tel[$t_tel] = 1;
      $tel_str = implode(',', array_keys($tel));
      */

      $tel_arr = array($tel1,$tel2,$tel3,$tel4,$tel5);
      $mobile = get_mobile($tel_arr);
      if (empty($mobile)) {
        echo "no mobile\n";
        continue;
      }

      // 過濾重覆
      if ($have[$subsid] == 1 || $haveC[$custid] == 1 || $haveT[$mobile] == 1) {
        echo "duplication\n";
        continue;
      }
      $have[$subsid]  = 1;
      $haveC[$custid] = 1;
      $haveT[$mobile] = 1;

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
        echo "no test mobile\n";
        continue;
      }
      */
      // for test

      $token = md5($so.','.$subsid.','.microtime(true).','.rand(100, 999));
      $code = '';
      while(1) {
        $cnt = 0;
        $code = substr(str_shuffle("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"), 0, 6);
        $sqlx = "select count(*) cnt from short_url where time >= date_sub(now(), interval 50 day) and token = '$code'";
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
      if ($so == '106') {
        if ($servicename == 'C HS')
          $sms_mesg = '您好，感謝您申辦大新店居家防護服務，誠摯的邀請您抽空填寫' . ($p_type == 0 ? '裝機':'維修') . '滿意度問卷 ' . $url;
        else if (in_array($servicename, array('2 CM','5 FTTB','7 EOC')))
          $sms_mesg = '您好，感謝您申辦大新店寬頻光纖上網服務，誠摯的邀請您抽空填寫' . ($p_type == 0 ? '裝機':'維修') . '滿意度問卷 ' . $url;
        else if (in_array($servicename, array('1 CATV','3 DSTB')))
          $sms_mesg = '您好，感謝您申辦大新店數位電視服務，誠摯的邀請您抽空填寫' . ($p_type == 0 ? '裝機':'維修') . '滿意度問卷 ' . $url;
      }
      else {
        if ($servicename == 'C HS')
          $sms_mesg = '您好，感謝您申辦凱擘大寬頻居家防護服務，誠摯的邀請您抽空填寫' . ($p_type == 0 ? '裝機':'維修') . '滿意度問卷 ' . $url;
        else if (in_array($servicename, array('2 CM','5 FTTB','7 EOC')))
          $sms_mesg = '您好，感謝您申辦凱擘大寬頻光纖上網服務，誠摯的邀請您抽空填寫' . ($p_type == 0 ? '裝機':'維修'). '滿意度問卷 ' . $url;
        else if (in_array($servicename, array('1 CATV','3 DSTB')))
          $sms_mesg = '您好，感謝您申辦' . $soname[$so] . '數位電視服務，誠摯的邀請您抽空填寫' . ($p_type == 0 ? '裝機':'維修') . '滿意度問卷 ' . $url;
      }
      if (empty($sms_mesg)) {
        echo "no sms_mesg\n";
        continue;
      }

      $deadline = date("Y-m-d",strtotime("+3 day")) . ' 23:59:59';
      $sqlQ = "insert into cust_quest_paper (so,subsid,p_id,createtime,deadline,url,token,custid,servicename,subsname,mobile,packagename,billitem,brokerkind,swversion,chargename2,worksheet,acceptname,worker1,finishtime,backcause,backcause1)
               values ('$so','$subsid','$p_id',now(),'$deadline','$url','$token','$custid','$servicename','$subsname','$mobile','$packagename','$billitem','$brokerkind','$swversion','$chargename4','$worksheet','$acceptname','$worker1','$finishtime','$backcause','$backcause1')";
      $dbhQ->exec($sqlQ);
      $cust_p_id = $dbhQ->lastInsertId();

      // SMS
      $sqlO = "insert into oss_sms (sys,sender,target,msg,so,subsid) values ('CTI','quest','$mobile','$sms_mesg','$so','$subsid')";
      $dbhS->exec($sqlO);

      echo "OK $cust_p_id\n";
      echo "$sqlQ\n$sqlO\n";
    }


    // OEMS單一事件 for 維修
    if (in_array($p_flag, array('1','2','3','4'))) {
      $sqlO = "
            select
              a.companyno,
              a.subsid,
              to_char(max(a.close_date),'yyyy/mm/dd hh24:mi:ss') close_date,
              to_char(min(a.create_date),'yyyy/mm/dd hh24:mi:ss') create_date,
              to_char(min(a.create_date)+(8/24),'yyyy/mm/dd hh24:mi:ss') book_date,
              max(a.type_name) type_name,
              max(a.subtype_name) subtype_name,
              max(a.account) account,
              max(b.account) reply
            from v_oems_subsid a,oems_tickets_log b
            where
                  a.companyno in ($so_str) and a.normal_flag='U'
              and a.close_date between to_date('".$show_date_begin."','yyyy/mm/dd hh24:mi:ss') and to_date('".$show_date_end."','yyyy/mm/dd hh24:mi:ss')
              and a.status='5105'
              and a.sid=b.sid
            group by a.companyno,a.subsid
            order by a.companyno,a.subsid
          ";
      echo "$sqlO\n";
      $sthO = $dbhO->query($sqlO);
      while ($rowO = $sthO->fetch(PDO::FETCH_ASSOC)) {
        $companyno = $rowO['COMPANYNO'];
        $subsid = $rowO['SUBSID'];
        $close_date = $rowO['CLOSE_DATE'];
        $create_date = $rowO['CREATE_DATE'];
        $book_date = $rowO['BOOK_DATE'];
        $type_name = $rowO['TYPE_NAME'];
        $subtype_name = $rowO['SUBTYPE_NAME'];
        $c_account = $rowO['ACCOUNT'];
        $r_account = $rowO['REPLY'];

        echo "$companyno,$subsid,$close_date,$type_name,$subtype_name,$c_account,$r_account\n";

        $cosssql =
        "
          select
            b.companyno,
            d.aliasname,
            b.custid,
            b.servicename servicename,
            b.subsname subsname,
            b.telenum01 telenum01,
            b.cellphone01 cellphone01,
            b.telenum02 telenum02,
            b.cellphone02 cellphone02,
            b.telenum03 telenum03,
            c.mscity+c.msdistrict city,
            c.addrname addrname,
            '".$type_name."' backcause,
            '".$subtype_name."' backcause1,
            '單一事件' cleancause,
            b.custcharacter custcharacter,
            '".$c_account."' createname,
            '".$r_account."' worker1,
            b.chargename2,
            b.packagename
         from ms0200 b with (nolock), ms0102 c with (nolock), cdcompany d with (nolock)
         where
               b.companyno=d.companyno
           and b.companyno=c.companyno
           and b.custid=c.custid and c.addrno='0'
           and b.servicename in ($servicename_sql)
           and b.companyno='$companyno'
           and b.subsid='$subsid'
        ";
        echo "$cosssql\n";
        $sthC = $dbhC->query($cosssql);
        while ($rowC = $sthC->fetch(PDO::FETCH_ASSOC)) {
          $companyno = $rowC['companyno'];
          $aliasname = $rowC['aliasname'];
          $custid = $rowC['custid'];
          $subsname = $rowC['subsname'];
          $servicename = $rowC['servicename'];
          $telenum01 = $rowC['telenum01'];
          $telenum02 = $rowC['telenum02'];
          $telenum03 = $rowC['telenum03'];
          $cellphone01 = $rowC['cellphone01'];
          $cellphone02 = $rowC['cellphone02'];
          $finishdate = str_replace("-","/",$rowC['finishdate']);
          $city = $rowC['city'];
          $addrname = $rowC['addrname'];
          $worksheet = $rowC['worksheet'];
          $backcause = $rowC['backcause'];
          $backcause1 = $rowC['backcause1'];
          $cleancause = $rowC['cleancause'];
          $custcharacter = $rowC['custcharacter'];
          $createname = $rowC['createname'];
          $worker1 = $rowC['worker1'];
          $chargename2 = $rowC['chargename2'];
          $packagename = $rowC['packagename'];

          $tel = array();
          $t_tel = filtertel($companyno, $telenum01);
          if (!empty($t_tel)) $tel[$t_tel] = 1;
          $t_tel = filtertel($companyno, $telenum02);
          if (!empty($t_tel)) $tel[$t_tel] = 1;
          $t_tel = filtertel($companyno, $telenum03);
          if (!empty($t_tel)) $tel[$t_tel] = 1;
          $t_tel = filtertel($companyno, $cellphone01);
          if (!empty($t_tel)) $tel[$t_tel] = 1;
          $t_tel = filtertel($companyno, $cellphone02);
          if (!empty($t_tel)) $tel[$t_tel] = 1;
          $tel_str = implode(',', array_keys($tel));

          echo "> $companyno,$subsname,>$tel_str\n";
        }

      }
    }

  }

  print_r($test_data);

  echo "\n" . 'Stop Time: ' . date("Y-m-d H:i:s") . "\n";
?>
