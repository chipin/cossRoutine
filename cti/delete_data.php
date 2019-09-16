<?php
  include_once('common.inc.php');

  $ora = GetDBH('CTI_MMCC');

  /*
  $sql = "select * from ocmp.master_log
          where to_char(modify_date, 'yyyymmdd') < to_char(sysdate-86,'yyyymmdd')
          and ROWNUM = 1";
  $sth = oci_parse($ora, $sql);
  oci_execute($sth);
  while ($row = oci_fetch_assoc($sth)) {
    print_r($row);
  }
  */

  /*
  $table_arr = array(
               'ocmp.master_log'                 => "delete from ocmp.master_log where to_char(modify_date, 'yyyymmdd') < to_char(sysdate - 90,'yyyymmdd')",
               'ocmp.ag_login_log'               => "delete from ocmp.ag_login_log where to_char(login_time, 'yyyymmdd') < to_char(sysdate - 1900,'yyyymmdd')",
               'ocmp.function_log'               => "delete from ocmp.function_log where to_char(process_time, 'yyyymmdd') < to_char(sysdate - 90,'yyyymmdd')",
               'ocmp.ivrcalllog_new'             => "delete from ocmp.ivrcalllog_new where to_char(create_date, 'yyyymmdd') < to_char(sysdate - 1200,'yyyymmdd')",
               'icare.mrs_log'                   => "delete from icare.mrs_log where to_char(create_date, 'yyyymmdd') < to_char(sysdate - 90,'yyyymmdd')",
               'icare.tb_error_record'           => "delete from icare.tb_error_record where to_char(create_date, 'yyyymmdd') < to_char(sysdate - 500,'yyyymmdd')",
               'dialer.tb_ftp_calllist'          => "delete from dialer.tb_ftp_calllist where lst_date < to_char(sysdate - 1800,'yyyymmdd')",
               'dialer.tb_ftp_callresult'        => "delete from dialer.tb_ftp_callresult where lst_date < to_char(sysdate - 1900,'yyyymmdd')",
               'dialer.tb_history_callresult'    => "delete from dialer.tb_history_callresult where lst_date < to_char(sysdate - 1800,'yyyymmdd')",
               'dialer.tb_history_callresultlog' => "delete from dialer.tb_history_callresultlog where lst_date < to_char(sysdate - 1900,'yyyymmdd')",
               'dialer.tb_outbound_log'          => "delete from dialer.tb_outbound_log where to_char(log_date, 'yyyymmdd') < to_char(sysdate - 180,'yyyymmdd')",
               'faxdb.fax_doc_log'               => "delete from faxdb.fax_doc_log where to_char(create_date, 'yyyymmdd') < to_char(sysdate - 180,'yyyymmdd')"
               );
  */

  // ocmp.ag_login_log 24 730
  // ocmp.ivrcalllog_new 6 186
  // icare.tb_error_record 6 186
  // dialer.tb_ftp_calllist 6 186
  // dialer.tb_ftp_callresult 24 730
  // dialer.tb_history_callresult 24 730
  // dialer.tb_history_callresultlog 24 730

  $table_arr = array(
               'ocmp.ag_login_log'               => "delete from ocmp.ag_login_log where to_char(login_time, 'yyyymmdd') < to_char(sysdate - 1500,'yyyymmdd')",
               'dialer.tb_ftp_calllist'          => "delete from dialer.tb_ftp_calllist where lst_date < to_char(sysdate - 1500,'yyyymmdd')",
               'dialer.tb_ftp_callresult'        => "delete from dialer.tb_ftp_callresult where lst_date < to_char(sysdate - 1500,'yyyymmdd')",
               'dialer.tb_history_callresult'    => "delete from dialer.tb_history_callresult where lst_date < to_char(sysdate - 1500,'yyyymmdd')",
               'dialer.tb_history_callresultlog' => "delete from dialer.tb_history_callresultlog where lst_date < to_char(sysdate - 1500,'yyyymmdd')"
               );

  foreach($table_arr as $kk => $vv) {
    echo "$kk\n";
    echo "=> $vv\n";

    $a = microtime(true);
    $sql = $vv;
    $sth = oci_parse($ora, $sql);
    oci_execute($sth);
    $b = microtime(true);
    $c = oci_num_rows($sth);
    echo "=> $c rows affected " . number_format($b-$a,2) . "s\n";
  }


?>

