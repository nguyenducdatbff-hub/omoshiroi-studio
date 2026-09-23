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

// Verify Jev Evaluator Panel elements exist in HTML template
assert(html.includes('id="evaluatorPanel"'), 'Evaluator panel exists in index.html');
assert(html.includes('id="contentProfileSelect"'), 'Content profile selector exists');
assert(html.includes('value="irasutoya_short"'), 'Default irasutoya_short profile exists');
assert(html.includes('value="anime_recap_edit"'), 'Anime recap profile exists');
assert(html.includes('value="asian_myth_3d"'), 'Asian myth 3D profile exists');
assert(html.includes('id="targetAudienceInput"'), 'Target audience input exists');
assert(html.includes('id="evaluateBtn"'), 'Evaluate button exists');
assert(html.includes('id="scorecardContainer"'), 'Scorecard container exists');
assert(html.includes('id="viralScoreNum"'), 'Viral score display exists');
assert(html.includes('id="classificationTag"'), 'Classification tag exists');
assert(html.includes('id="dimensionsContainer"'), 'Dimensions container exists');
assert(html.includes('id="recommendationsList"'), 'Recommendations list exists');
assert(html.includes('id="evalErrorBox"'), 'Error box exists');
assert(html.includes('id="evalStaleBanner"'), 'Stale banner exists');
assert(html.includes('id="evaluationDownloadLink"'), 'Evaluation download link exists');

// Verify evaluator panel is positioned before renderBtn
const evalPos = html.indexOf('id="evaluatorPanel"');
const renderPos = html.indexOf('id="renderBtn"');
assert(evalPos > 0 && renderPos > evalPos, 'Evaluator panel is positioned before render button');

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
  vm.runInContext('updateKeyStatus()', context);
  assert.match(elements.keyStatusText.innerHTML, /Gemini Key|đã lưu/i);

  const button = { innerHTML: 'Tạo Kịch Bản', disabled: false };
  await vm.runInContext('generateWithAI', context)(button);
  assert.equal(notices.has('hidden'), false, 'Gemini failure is visible beside topic input');
  assert.match(elements.aiModeNotice.textContent, /403/);
  assert.equal(alerts.length, 0, 'No alert-only error');
  assert.equal(button.disabled, false);
}

async function testJevEvaluatorFlow() {
  const scorecardClasses = new Set(['hidden']);
  const staleClasses = new Set(['hidden']);
  const errorClasses = new Set(['hidden']);
  const statusBadge = { innerText: '', className: '' };

  elements.titleSubInput = { value: '【裁判】迷惑テロの末路' };
  elements.titleMainInput = { value: 'サクッと笑える' };
  elements.moralLessonInput = { value: 'ネットの10秒、借金地獄' };
  elements.contentProfileSelect = { value: 'irasutoya_short' };
  elements.targetAudienceInput = { value: 'Người xem anime' };
  elements.evalStatusBadge = statusBadge;
  elements.viralScoreNum = { innerText: '', className: '' };
  elements.scoreBadgeCircle = { className: '' };
  elements.classificationTag = { innerText: '', className: '' };
  elements.classificationDesc = { innerText: '' };
  elements.evalModelTag = { innerText: '' };
  elements.overallConfidenceText = { innerText: '' };
  elements.evaluatedAtText = { innerText: '' };
  elements.dimensionsContainer = { innerHTML: '' };
  elements.recommendationsList = { innerHTML: '' };
  elements.scorecardContainer = {
    classList: {
      add: name => scorecardClasses.add(name),
      remove: name => scorecardClasses.delete(name),
      has: name => scorecardClasses.has(name)
    }
  };
  elements.evalStaleBanner = {
    classList: {
      add: name => staleClasses.add(name),
      remove: name => staleClasses.delete(name),
      has: name => staleClasses.has(name)
    }
  };
  elements.evalErrorBox = {
    classList: {
      add: name => errorClasses.add(name),
      remove: name => errorClasses.delete(name),
      has: name => errorClasses.has(name)
    }
  };
  elements.evalErrorTitle = { innerText: '' };
  elements.evalErrorMessage = { innerText: '', innerHTML: '' };

  // 1. Test successful evaluation
  const mockEval = {
    status: 'ok',
    model: 'jev-latest',
    rubric_version: 'viral-short-v1',
    viral_score: 82,
    classification: 'recommended',
    overall_confidence: 0.88,
    dimensions: {
      hook_strength: { score: 3.5, confidence: 0.9, uncertain: false },
      curiosity_emotion: { score: 3.0, confidence: 0.85, uncertain: false },
      retention_payoff: { score: 3.2, confidence: 0.9, uncertain: false },
      share_comment: { score: 3.5, confidence: 0.85, uncertain: false }
    },
    weakest_dimension: 'curiosity_emotion',
    recommendations: [
      { code: 'RAISE_CURIOSITY_STAKES', dimension: 'curiosity_emotion', message: 'Trì hoãn lời giải để tăng tò mò.' }
    ],
    evaluated_at: '2026-09-23T12:00:00Z',
    input_fingerprint: 'sha256:testhash'
  };

  context.fetch = async () => ({
    ok: true,
    json: async () => mockEval
  });

  const btn = { innerHTML: 'Đánh Giá', disabled: false };
  await vm.runInContext('evaluateScript', context)(btn);

  assert.equal(scorecardClasses.has('hidden'), false, 'Scorecard is shown after successful evaluation');
  assert.equal(elements.viralScoreNum.innerText, 82, 'Viral score correctly displayed');
  assert.match(elements.classificationTag.innerText, /Recommended/i, 'Classification tag displayed');
  assert.match(elements.dimensionsContainer.innerHTML, /Hook/i, 'Dimension bars rendered');
  assert.match(elements.recommendationsList.innerHTML, /RAISE_CURIOSITY_STAKES/, 'Recommendation rendered');
  assert.equal(btn.disabled, false, 'Evaluate button re-enabled');

  // 2. Test Stale detection
  vm.runInContext('markEvaluationStale()', context);
  assert.equal(staleClasses.has('hidden'), false, 'Stale banner shown when marked stale');
  assert.equal(scorecardClasses.has('opacity-60'), true, 'Scorecard dimmed when stale');
  assert.match(statusBadge.innerText, /Cần chấm lại/, 'Badge indicates stale');
  assert.equal(vm.runInContext('latestEvaluation.stale', context), true, 'latestEvaluation object marked stale');

  // 3. Test Fail-open on TypeSafe missing key (503)
  context.fetch = async () => ({
    ok: false,
    status: 503,
    json: async () => ({ status: 'error', error: { code: 'TYPESAFE_NOT_CONFIGURED', message: 'Chưa cấu hình API Key' } })
  });

  await vm.runInContext('evaluateScript', context)(btn);
  assert.equal(errorClasses.has('hidden'), false, 'Error box is visible on 503');
  assert.match(elements.evalErrorMessage.innerHTML, /TYPESAFE_API_KEY/, 'Helpful configuration instruction shown');
  assert.equal(btn.disabled, false, 'Evaluate button re-enabled');
}

async function runAllTests() {
  await testGeminiErrorFeedback();
  await testJevEvaluatorFlow();
  console.log('UI smoke checks passed');
}

runAllTests().catch(error => { console.error(error); process.exitCode = 1; });
