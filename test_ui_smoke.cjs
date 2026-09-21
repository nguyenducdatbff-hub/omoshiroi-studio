const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('web/templates/index.html', 'utf8');
const script = html.match(/<!-- App State & Interactivity Scripts -->\s*<script>([\s\S]*?)<\/script>/)[1].replace(/\s*init\(\);\s*$/, '');
const elements = { dialogueList: { innerHTML: '' }, matchupGrid: { innerHTML: '' } };
const context = {
  document: { getElementById: id => elements[id] },
  console,
};
vm.createContext(context);
vm.runInContext(script, context);
vm.runInContext(`
  matchups = [{id:'courtroom', title:'Court', speaker_a:'judge', speaker_b:'prisoner', icon:'⚖️'}];
  characters = {
    judge: {name_jp:'裁判官', name_vi:'Thẩm phán'},
    prisoner: {name_jp:'被告', name_vi:'Bị cáo'}
  };
  currentDialogue = [{speaker:'judge', emotion:'normal', text:'\" onfocus=\"alert(1)', text_vi:'<img src=x onerror=alert(1)>'}];
  renderDialogueEditor();
  renderMatchupGrid();
`, context);
assert(!elements.dialogueList.innerHTML.includes('value="" onfocus='), 'Japanese text escaped in input');
assert(!elements.dialogueList.innerHTML.includes('<img src=x'), 'Vietnamese text escaped in input');
assert.match(elements.matchupGrid.innerHTML, /<button\b/, 'matchup is keyboard operable');
assert.match(elements.matchupGrid.innerHTML, /aria-pressed="true"/, 'selected matchup exposed to screen readers');

async function testGeminiErrorFeedback() {
  const notices = new Set(['hidden']);
  const alerts = [];
  elements.aiTopicInput = { value: 'nhân viên trễ deadline' };
  elements.aiModeNotice = {
    textContent: '',
    classList: {
      add: name => notices.add(name),
      remove: name => notices.delete(name),
      toggle: (name, on) => on ? notices.add(name) : notices.delete(name),
    },
  };
  elements.keyStatusText = { innerHTML: '', innerText: '' };
  elements.geminiKeyInput = { value: '' };
  context.localStorage = { getItem: () => 'FAKE-KEY' };
  context.fetch = async () => ({ ok: false, json: async () => ({ detail: 'Gemini từ chối quyền truy cập (403).' }) });
  context.alert = message => alerts.push(message);
  vm.runInContext('updateKeyStatus()', context);
  assert.match(elements.keyStatusText.innerHTML, /đã lưu/i);
  assert.doesNotMatch(elements.keyStatusText.innerHTML, /✓/);

  const button = { innerHTML: 'Tạo Kịch Bản', disabled: false };
  await vm.runInContext('generateWithAI', context)(button);
  assert.equal(notices.has('hidden'), false, 'Gemini failure is visible beside topic input');
  assert.match(elements.aiModeNotice.textContent, /403/);
  assert.equal(alerts.length, 0, 'No alert-only error');
  assert.equal(button.disabled, false);
}

testGeminiErrorFeedback().then(() => console.log('UI smoke checks passed')).catch(error => { console.error(error); process.exitCode = 1; });
