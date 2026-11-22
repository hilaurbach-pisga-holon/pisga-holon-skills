/**
 * קיר תוכנית הטיסה · מרכז הל"ה למיומנויות, פסג"ה חולון
 * הקוד הזה רק שומר וקורא את התשובות בגיליון.
 * הטופס והקיר עצמם נמצאים באתר המרכז ב-GitHub.
 */
var SHEET_NAME = 'תוצרים';
var HEAD = ['זמן', 'שולחן', 'שם הקבוצה', 'מיומנות', 'יכולת', 'הגדרה במשפט', 'מתגלה', 'מתפתח/ת', 'מסוגל/ת', 'מיומן/ת', 'מעבר: מאיזו רמה', 'מעבר: מה עושים בכיתה'];
var KEYS = ['ts', 'table', 'group', 'skill', 'ability', 'def', 'l1', 'l2', 'l3', 'l4', 'tfrom', 'tmove'];

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
  }
  return sh;
}

function clean_(v, max) {
  return String(v == null ? '' : v).replace(/[\u0000-\u0008\u000B-\u001F]/g, '').trim().slice(0, max || 400);
}

/** הקיר קורא מכאן */
function doGet() {
  var sh = sheet_();
  var n = sh.getLastRow();
  var rows = [];
  if (n > 1) {
    rows = sh.getRange(2, 1, n - 1, HEAD.length).getValues()
      .filter(function (r) { return r[1] !== ''; })
      .map(function (r) {
        var o = {};
        KEYS.forEach(function (k, i) { o[k] = r[i] instanceof Date ? String(r[i].getTime()) : String(r[i]); });
        return o;
      });
    rows.sort(function (a, b) { return Number(a.table) - Number(b.table); });
  }
  return json_({ rows: rows });
}

/** הטופס שולח לכאן. שולחן ששולח שוב מעדכן את השורה שלו. */
function doPost(e) {
  try {
    var d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var table = clean_(d.table, 3).replace(/\D/g, '');
    if (!table) return json_({ ok: false, error: 'חסר מספר שולחן' });
    var row = [new Date(), table, clean_(d.group, 60), clean_(d.skill, 120), clean_(d.ability, 160), clean_(d.def, 300),
      clean_(d.l1), clean_(d.l2), clean_(d.l3), clean_(d.l4), clean_(d.tfrom, 40), clean_(d.tmove, 300)];
    if (!row[6] && !row[7] && !row[8] && !row[9]) return json_({ ok: false, error: 'חסרות הרמות' });
    var lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try {
      var sh = sheet_();
      var n = sh.getLastRow(), at = -1;
      if (n > 1) {
        var t = sh.getRange(2, 2, n - 1, 1).getValues();
        for (var i = 0; i < t.length; i++) if (String(t[i][0]) === table) { at = i + 2; break; }
      }
      if (at > 0) sh.getRange(at, 1, 1, row.length).setValues([row]);
      else sh.appendRow(row);
    } finally {
      lock.releaseLock();
    }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  }
}
