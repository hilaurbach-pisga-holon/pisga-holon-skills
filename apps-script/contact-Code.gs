/**
 * טופס "כתבו לנו" · מרכז הל"ה למיומנויות, פסג"ה חולון
 * הקוד שומר כל פנייה כשורה בגיליון "פניות", ויכול לשלוח הודעת דוא"ל על כל פנייה חדשה.
 * הטופס עצמו נמצא באתר המרכז (contact.html).
 */

// לאן לשלוח התראה על פנייה חדשה. אפשר כמה כתובות מופרדות בפסיק. ריק = בלי התראה.
var NOTIFY = 'pisgaholon@taded.org.il';

var SHEET_NAME = 'פניות';
var HEAD = ['זמן', 'שם', 'תפקיד', 'בית ספר', 'דוא"ל', 'טלפון', 'סוג הפנייה', 'מיומנות', 'שכבה', 'הפנייה', 'הגיע מעמוד', 'סטטוס', 'מי מטפל', 'הערות'];

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function sheet_() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEAD);
    sh.setFrozenRows(1);
    sh.setRightToLeft(true);
    sh.getRange(1, 1, 1, HEAD.length).setFontWeight('bold').setBackground('#29275E').setFontColor('#FFFFFF');
    sh.setColumnWidth(10, 420);
    var rule = SpreadsheetApp.newDataValidation().requireValueInList(['חדש', 'בטיפול', 'נענה'], true).build();
    sh.getRange(2, 12, 1000, 1).setDataValidation(rule);
  }
  return sh;
}

function clean_(v, max) {
  // מסיר תווי בקרה, ומונע נוסחאות בגיליון (תא שמתחיל ב-= + - @)
  var s = String(v == null ? '' : v).replace(/[\u0000-\u0008\u000B-\u001F]/g, '').trim().slice(0, max || 200);
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function doGet() {
  return json_({ ok: true, service: 'contact' });
}

function doPost(e) {
  try {
    var d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (d.website) return json_({ ok: true }); // מלכודת לרובוטים
    var row = [new Date(), clean_(d.name, 80), clean_(d.role, 80), clean_(d.school, 120), clean_(d.email, 120), clean_(d.phone, 30),
      clean_(d.kind, 60), clean_(d.item, 120), clean_(d.grade, 30), clean_(d.msg, 2000), clean_(d.page, 300), 'חדש', '', ''];
    if (!row[1]) return json_({ ok: false, error: 'חסר שם' });
    if (!row[4] && !row[5]) return json_({ ok: false, error: 'חסר דוא"ל או טלפון' });
    if (!row[9]) return json_({ ok: false, error: 'חסר תוכן הפנייה' });
    var lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try { sheet_().appendRow(row); } finally { lock.releaseLock(); }
    if (NOTIFY) {
      try {
        MailApp.sendEmail({
          to: NOTIFY,
          subject: 'פנייה חדשה באתר מרכז הל"ה: ' + row[6],
          body: ['שם: ' + row[1], 'תפקיד: ' + row[2], 'בית ספר: ' + row[3], 'דוא"ל: ' + row[4], 'טלפון: ' + row[5],
            'סוג: ' + row[6], 'מיומנות: ' + (row[7] || 'כללי'), 'שכבה: ' + row[8], '', row[9], '',
            'כל הפניות: ' + SpreadsheetApp.getActive().getUrl()].join('\n'),
          replyTo: row[4] || undefined
        });
      } catch (mailErr) { /* הפנייה כבר נשמרה בגיליון */ }
    }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  }
}
