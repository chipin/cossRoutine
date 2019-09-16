<?php
  /*
    請使用UTF-8 without BOM編碼
    0 未收
    1 正常
    2 停機
    3 已拆
    4 註銷
    5 促銷中
    6 裝機中
    7 待拆中
    8 欠費中
    9 移機中
    A 已關機
    B 待關機

    1 裝機
    5 維修
    6 移機
    9 立即開通
    C 換機
    N 更換產品
    => QOS

    3 拆機
    4 停機
    A 欠費關機
    A 關機
    D 欠費關機
    D 關機
    => ALOCK
  */
  include_once('common.inc.php');

  $now = date("Y-m-d H:i:s");
  echo "START: $now\n";

  $tday = date("Ymd");
  $yday = date("Y-m-d",strtotime('-1 day'));
  //$yday = '2014-09-04';

  //$msoAry = array('CG'=>'CGCossMS','KBRO'=>'kbroCossMS');
  $msoAry = array('TFM'=>'TFMCossMS','KBRO'=>'kbroCossMS','CG'=>'CGCossMS');



  $table = 'custdata_dstb';

  foreach ($msoAry as $mso=>$conn){


    $dbh = GetDBH($conn,'return');

    if (stristr($dbh, 'error') || empty($dbh)) {
      echo "$dbh\n";
      continue;
    }

    $myd = GetDBH('ISC_M','','return');
    if (stristr($myd, 'error') || empty($myd)) {
      echo "$myd\n";
      continue;
    }


    //
    $custall = array();

    //設備紀錄
    $sql = "select a.companyno,a.subsid from ms0211 a with(nolock) inner join ms0040 b with(nolock)
            on a.companyno = b.companyno and a.chargename = b.chargename
            where substring(b.servicename,1,1) = '3' and b.chargekind = '50' and b.stopyn = 'N'
            and a.createtime  >= '$yday 00:00:00' ";
    $sth = mssql_query($sql, $dbh);
    while ($row = mssql_fetch_assoc($sth)) {
      $row = strfilter($row);
      array_push($custall, $row['subsid']);

    }


    $sql = "select companyno,subsid from ms0200 with (nolock)
            where  substring(servicename,1,1) = '3' and
            (
              createtime >= '$yday 00:00:00' or updatetime >= '$yday 00:00:00' or tiestart >= '$yday 00:00:00' or instdate >= '$yday 00:00:00' or
              stopdate >= '$yday 00:00:00' or haltdate>= '$yday 00:00:00' or recoverdate >= '$yday 00:00:00' or movedate >= '$yday 00:00:00' or
               discntdate >= '$yday 00:00:00' or connectdate >= '$yday 00:00:00' or haltendd >= '$yday 00:00:00')";
    echo $sql . "\n";
    $sth = mssql_query($sql, $dbh);
    while ($row = mssql_fetch_assoc($sth)) {
      $row = strfilter($row);
      array_push($custall, $row['subsid']);
    }

    $custall = array_unique($custall); // 去掉重覆


    // LOCK
    $sql = "lock table $table write";
    echo "$sql\n";
    mysql_query($sql, $myd);


    //
    echo '異動數: ' . count($custall) . "\n";
    print_r($custall);
    while (count($custall) > 0) {
      $a1 = $a2 = array();
      $a1 = array_slice($custall, 0, 500); // 前500筆
      $a2 = array_splice($custall, 500); // 其餘的筆數
      $custall = $a2;

      if (count($a1) > 0) {
        $aa = "'" . implode("','", $a1) . "'";
        //echo "$aa\n";


        $sql = "select
                b.companyno,b.subsid,b.servicename,b.custstatus,substring(b.custstatus,1,1) stat,b.singlesn,b.packagename,b.billitem,z.actdate,z.oldpackage,z.oldcharge,z.newpackage,z.newcharge,b.swversion
                from ms0102 a with (nolock)
                inner join ms0200 b with (nolock) on b.companyno=a.companyno and b.custid=a.custid  and substring(b.servicename,1,1) = '3'
                left join (
                  select x.companyno,x.subsid,x.msflag,convert(varchar(8),x.startdate,112) startdate,case when x.actdate is not null and x.actdate <> '' then convert(varchar(8),x.actdate,112) else convert(varchar(8),x.startdate,112) end actdate,x.oldpackage,x.oldcharge,x.newpackage,x.newcharge
                  from ms0216 x with (nolock)
                  inner join (
                    select m.companyno,m.subsid,max(m.recvno) recvno from ms0216 m with (nolock)
                    inner join ms0200 n with (nolock) on n.companyno=m.companyno and n.subsid=m.subsid  and substring(n.servicename,1,1) = '3'
                    where  m.subsid in ($aa) group by m.companyno,m.subsid
                  ) y on y.companyno=x.companyno and y.subsid=x.subsid and y.recvno=x.recvno
                  where  x.subsid in ($aa) and x.msflag in ('1 正常','3 原價升級')
                ) z on z.companyno=b.companyno and z.subsid=b.subsid
                where  a.addrno='0' and b.subsid in ($aa)";
        echo "\n" . $sql . "\n";
        $sth = mssql_query($sql, $dbh);
        while ($row = mssql_fetch_assoc($sth)) {
          $row = strfilter($row);

          $companyno = $row['companyno'];
          $subsid = $row['subsid'];
          $servicename = $row['servicename'];
          $custstatus = $row['custstatus'];
          $stat = $row['stat'];
          $singlesn = $row['singlesn'];
          $packagename = $row['packagename'];
          $billitem = $row['billitem'];
          $actdate = $row['actdate'];
          $oldpackage = $row['oldpackage'];
          $oldcharge = $row['oldcharge'];
          $newpackage = $row['newpackage'];
          $newcharge = $row['newcharge'];
          $swversion = $row['swversion'];


          echo $companyno . ' ' . $subsid . ' ' . $custstatus . ' ' . $singlesn . ' ' . $packagename . ' ' . $billitem . "\n";

          if (!empty($packagename) && !empty($billitem) && !empty($oldpackage) && !empty($oldcharge) && !empty($newpackage) && !empty($newcharge)) {
            if ($packagename == $oldpackage && $billitem == $oldcharge) { // 促案變更未過帳(現行方案=舊方案,現行收費=舊收費)
              if ($tday >= $actdate) { // 已生效
                echo 'new: ' . $oldpackage . ' ' . $oldcharge . ' <' . $actdate . '> ' . $newpackage . ' ' . $newcharge . "\n";
                $packagename = $newpackage;
                $billitem    = $newcharge;
              }
            }
            else if ($packagename == $newpackage && $billitem == $newcharge) { // 促案變更已過帳(現行方案=新方案,現行收費=新收費)
              if ($actdate > $tday) { // 未生效
                echo 'old: ' . $oldpackage . ' ' . $oldcharge . ' <' . $actdate . '> ' . $newpackage . ' ' . $newcharge . "\n";
                $packagename = $oldpackage;
                $billitem    = $oldcharge;
              }
            }
          }


          if (in_array($stat, array('3','4','5'))) {
            $sql2 = "delete from $table where companyno='$companyno' and subsid='$subsid'";
            echo "$sql2\n";
            mysql_query($sql2, $myd);
          }else{
            $sql2 = "insert into $table (companyno,subsid,servicename,custstatus,singlesn,billitem,updatetime,swversion) values ('$companyno','$subsid','$servicename','$custstatus','$singlesn','$billitem',now(),'$swversion') on duplicate key update servicename=values(servicename),custstatus=values(custstatus),singlesn=values(singlesn),billitem=values(billitem),updatetime=values(updatetime),swversion=values(swversion)";
            echo "$sql2\n";
            mysql_query($sql2, $myd);
          }


        }
      }
    }


    // UNLOCK
    $sql = "unlock tables";
    echo "$sql\n";
    mysql_query($sql, $myd);

    mssql_close($dbh);
    mysql_close($myd);

  }

  $now = date("Y-m-d H:i:s");
  echo "END: $now\n";
?>
