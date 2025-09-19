from model.SQL_conn import (get_mysql_conn, get_ms_sql_conn)

def _extract_marks_from_current_set(cursor, idx=5):
    """Read current result set, return normalized set of marks from column idx."""
    rows = cursor.fetchall()
    return {str(row[idx]).strip() for row in rows}

def _drain_all_remaining_sets(cursor):
    try:
        while cursor.nextset():
            pass
    except Exception:
        pass

def build_pkg_content_list(job_code: int, pkg_code: str):
    with get_ms_sql_conn() as msconn, get_mysql_conn() as mysqlconn:

        with msconn.cursor() as mscursor:
            mscursor.execute("EXEC fabtracker.getparts ?, ?, null", (job_code, pkg_code))
            parts = sorted({str(row[5]).strip() for row in mscursor.fetchall()})

        with mysqlconn.cursor() as mysqlcursor:
            mysqlcursor.execute("CALL fabrication.MFC_GetMain_InPackage(%s, %s)", (job_code, pkg_code))
            main_marks = sorted(_extract_marks_from_current_set(mysqlcursor, idx=5))
            _drain_all_remaining_sets(mysqlcursor)

            if not parts:
                used_stored = False
                try:
                    mysqlcursor.callproc("fabrication.MFC_GetParts_InPackage", (job_code, pkg_code))
                    rows = []
                    if hasattr(mysqlcursor, "stored_results"):
                        for rs in mysqlcursor.stored_results():
                            rows.extend(rs.fetchall())
                        used_stored = True
                except Exception:
                    pass

                if not used_stored:
                    mysqlcursor.execute("CALL fabrication.MFC_GetParts_InPackage(%s, %s)", (job_code, pkg_code))
                    rows = mysqlcursor.fetchall()
                    _drain_all_remaining_sets(mysqlcursor)

                if rows:
                    parts = sorted({str(r[6]).strip() for r in rows})

    return main_marks, parts