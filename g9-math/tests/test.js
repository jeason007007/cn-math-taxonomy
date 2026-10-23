/* 引擎自测：node tests/test.js */
'use strict';

global.window = global;
global.localStorage = {
  _d: {},
  getItem: function (k) { return Object.prototype.hasOwnProperty.call(this._d, k) ? this._d[k] : null; },
  setItem: function (k, v) { this._d[k] = String(v); },
  removeItem: function (k) { delete this._d[k]; }
};
require('../data/bundle.js');
require('../assets/core.js');

const E = global.Engine;
const D = global.CN_DATA;

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? '  -> ' + extra : '')); }
}

console.log('\n== 数据完整性 ==');
/* 上游会更新，所以不写死具体数字：跟 meta 自洽 + 卡下限防缩水 */
ok('知识点数 = meta.closureCount', D.topics.length === D.meta.closureCount,
  D.topics.length + ' vs ' + D.meta.closureCount);
ok('知识点数 >= 386（上游 2026-10-22 版）', D.topics.length >= 386, D.topics.length);
ok('初三本体 = 82', D.topics.filter(t => t.isCore).length === 82);
ok('先修边 = meta.depCount', D.deps.length === D.meta.depCount,
  D.deps.length + ' vs ' + D.meta.depCount);
ok('先修边 >= 664（上游 2026-10-22 版）', D.deps.length >= 664, D.deps.length);
ok('没有物理/英语点混入',
  D.topics.every(t => !/^cn[pe]_/.test(t.id)),
  D.topics.filter(t => /^cn[pe]_/.test(t.id)).map(t => t.id).slice(0, 5).join(','));
ok('每题都有解析', D.questions.every(q => q.explanation && q.explanation.length > 0));
ok('每题都有答案', D.questions.every(q => q.answer !== undefined && String(q.answer).length > 0));
ok('初三知识点都有题', D.topics.filter(t => t.isCore).every(t => E.questionsOf(t.id).length > 0));

console.log('\n== 先修链 ==');
const chain = E.chainTo('cnm_221'); // 配方法
ok('配方法的先修链非空', chain.length > 1, chain.length);
ok('链尾是配方法自己', chain[chain.length - 1] === 'cnm_221');
ok('链从低年级到高年级', chain.every((id, i) =>
  i === 0 || E.topic(chain[i - 1]).grade <= E.topic(id).grade),
  chain.map(id => E.topic(id).name + '/' + E.topic(id).grade).join(' → '));

console.log('\n== 出卷 ==');
const paper = E.generatePaper({
  scope: { semesters: ['上', '下'] },
  count: 25,
  ratio: { basic: 0.2, standard: 0.45, advanced: 0.35 },
  hardMode: true,
  mode: 'normal',
  usedQids: {},
  topicStats: {},
  seed: 12345
});
ok('题数 = 25', paper.count === 25, paper.count);
ok('无重复题', new Set(paper.items.map(i => i.qid)).size === paper.count);
ok('题号连续 1..n', paper.items.every((it, i) => it.no === i + 1));
ok('全是初三知识点', paper.items.every(it => E.topic(it.topicId).isCore));
const secSum = paper.sections.reduce((a, s) => a + s.items.length, 0);
ok('分卷题数合计 = 总题数', secSum === paper.count, secSum + ' vs ' + paper.count);
const advRatio = paper.items.filter(i => i.difficulty === 'advanced').length / paper.count;
ok('提高题占比 > 25%', advRatio > 0.25, (advRatio * 100).toFixed(0) + '%');

console.log('\n== 出卷：章节均衡 ==');
const chCount = {};
paper.items.forEach(it => {
  const c = E.topic(it.topicId).chapter;
  chCount[c] = (chCount[c] || 0) + 1;
});
const maxCh = Math.max.apply(null, Object.values(chCount));
ok('单章不超过 5 题', maxCh <= 5, '最大 ' + maxCh + ' 题');

console.log('\n== 出卷：可复现 ==');
const p2 = E.generatePaper({
  scope: { semesters: ['上', '下'] }, count: 25,
  ratio: { basic: 0.2, standard: 0.45, advanced: 0.35 }, hardMode: true,
  mode: 'normal', usedQids: {}, topicStats: {}, seed: 12345
});
ok('同种子出同一套题', JSON.stringify(paper.items) === JSON.stringify(p2.items));

console.log('\n== 诊断 ==');
const test = {
  items: paper.items,
  wrong: paper.items.slice(0, 4).map(i => i.qid)
};
const r = E.diagnose(test, { topicStats: {} });
ok('总览题数正确', r.summary.total === 25);
ok('错题数正确', r.summary.wrong === 4);
ok('有直接薄弱点', r.direct.length > 0, r.direct.length);
ok('有根因候选', r.roots.length > 0, r.roots.length);
ok('根因有置信度', r.roots.every(x => ['高', '中', '低'].includes(x.confidence)));
ok('根因有影响面', r.roots.every(x => typeof x.downstream === 'number'));
ok('链条数与薄弱点数一致', r.chains.length === r.direct.length);
ok('链条都从低年级开始', r.chains.every(c =>
  c.path.length === 0 || E.topic(c.path[0].id).grade <= 9));
ok('章节表现有正确率', r.chapters.every(c => c.rate >= 0 && c.rate <= 100));

console.log('\n== 诊断：已掌握的先修点应被排除 ==');
const rootId = r.roots[0].topicId;
const stateProven = { topicStats: {} };
stateProven.topicStats[rootId] = {
  okStreak: 2, lastOkAt: '2026-10-21T10:00:00Z', lastWrongAt: null
};
const r2 = E.diagnose(test, stateProven);
ok('已掌握的点不再作为根因', !r2.roots.some(x => x.topicId === rootId), rootId);

console.log('\n== 讲解卡 ==');
const L = E.buildLesson(r.roots[0].topicId, test);
ok('讲解卡有名称', !!L.name);
ok('讲解卡有描述', !!L.description);
ok('讲解卡有掌握标准', L.mastery.length > 0);
ok('讲解卡有先修链', L.chain.length > 0);
ok('讲解卡有例题', !!L.diagnostic);
ok('讲解卡有同类练习', L.practice.length > 0);

console.log('\n== 根因验证卷 ==');
const probePaper = E.generatePaper({
  scope: { semesters: ['上', '下'] },
  count: 12,
  ratio: { basic: 0.3, standard: 0.5, advanced: 0.2 },
  mode: 'probe',
  probe: r.roots.slice(0, 4).map(x => x.topicId),
  usedQids: {},
  topicStats: {},
  seed: 999
});
ok('验证卷只考根因点', probePaper.items.every(it => it.isProbe), probePaper.probeCount);
ok('验证卷可以出到非初三的点',
  probePaper.items.some(it => !E.topic(it.topicId).isCore) ||
  r.roots.slice(0, 4).every(x => x.isCore),
  probePaper.items.map(i => E.topic(i.topicId).grade).join(','));

console.log('\n== 去重 ==');
const used = {};
paper.items.forEach(i => { used[i.qid] = 1; });
const p3 = E.generatePaper({
  scope: { semesters: ['上', '下'] }, count: 25,
  ratio: { basic: 0.2, standard: 0.45, advanced: 0.35 }, hardMode: true,
  mode: 'normal', usedQids: used, topicStats: {}, seed: 12345
});
const overlap = p3.items.filter(i => used[i.qid]).length;
ok('已做过的题基本不重复', overlap <= 3, overlap + ' 道重复');

console.log('\n== 解答题 ==');
const shAll = D.questions.filter(q => q.type === 'short' && q.origin === 'self');
ok('自编解答题已入包', shAll.length === 55, shAll.length);
ok('解答题都有解题过程', shAll.every(q => q.solution && q.solution.length > 20));
ok('解答题都有分值', shAll.every(q => q.points >= 6));
ok('解答题都有答题空间', shAll.every(q => q.space >= 140));
ok('解答题都指向初三知识点', shAll.every(q => E.topic(q.topicId) && E.topic(q.topicId).isCore));
ok('解答题 id 不重复', new Set(shAll.map(q => q.id)).size === shAll.length);

const pSh = E.generatePaper({
  scope: { semesters: ['上', '下'] },
  count: 25, shortCount: 3,
  ratio: { basic: 0.2, standard: 0.45, advanced: 0.35 }, hardMode: true,
  mode: 'normal', usedQids: {}, topicStats: {}, seed: 4242
});
const shortItems = pSh.items.filter(i => i.type === 'short' || i.type === 'self');
ok('解答题数量符合要求', shortItems.length === 3, shortItems.length);
ok('总题数仍为 25', pSh.count === 25, pSh.count);
ok('解答题排在最后', pSh.items.slice(-3).every(i => i.type === 'short'));
ok('解答题带分值', shortItems.every(i => i.points >= 6));
ok('解答题不重复知识点', new Set(shortItems.map(i => i.topicId)).size === 3);
ok('分卷合计 = 25', pSh.sections.reduce((a, s) => a + s.items.length, 0) === 25);
ok('解答题单独成一节', pSh.sections[pSh.sections.length - 1].key === 'short');

const pSh0 = E.generatePaper({
  scope: { semesters: ['上', '下'] }, count: 20, shortCount: 0,
  ratio: { basic: 0.4, standard: 0.4, advanced: 0.2 },
  mode: 'normal', usedQids: {}, topicStats: {}, seed: 1
});
ok('shortCount=0 时全是客观题', pSh0.items.every(i => i.type === 'choice' || i.type === 'numeric'));

const pSh5 = E.generatePaper({
  scope: { semesters: ['上', '下'] }, count: 20, shortCount: 5,
  ratio: { basic: 0.3, standard: 0.4, advanced: 0.3 },
  mode: 'normal', usedQids: {}, topicStats: {}, seed: 9
});
ok('shortCount=5 时出 5 道解答题',
  pSh5.items.filter(i => i.type === 'short').length === 5,
  pSh5.items.filter(i => i.type === 'short').length);

console.log('\n== 状态流转 ==');
require('../assets/store.js');
const S = global.Store;
S.reset();
const t1 = S.createTest(paper, '全册');
ok('新建卷未批改', !t1.done);
ok('currentTest 拿到待批改卷', S.currentTest() && S.currentTest().id === t1.id);

const w1 = paper.items.slice(0, 3).map(i => i.qid);
S.submitGrade(t1.id, w1);
let st1 = S.stats();
ok('批改后计入统计', st1.testCount === 1 && st1.totalWrong === 3, JSON.stringify(st1));
const blindAfter = S.blindSpots();
ok('盲点被记录', blindAfter.length > 0, blindAfter.length);

/* 重新提交同一份卷，统计不应翻倍 */
S.submitGrade(t1.id, w1);
const st2 = S.stats();
ok('重复提交不重复累计', st2.testCount === 1 && st2.totalQ === st1.totalQ,
  JSON.stringify(st2) + ' vs ' + JSON.stringify(st1));

/* 改判为全对，盲点应清空 */
S.submitGrade(t1.id, []);
ok('改判全对后盲点清零', S.blindSpots().length === 0, S.blindSpots().length);

/* 做过的题应进入 usedQids */
ok('做过的题被记住', Object.keys(S.state.usedQids).length === paper.count,
  Object.keys(S.state.usedQids).length + ' vs ' + paper.count);

console.log('\n== 导出 / 导入 ==');
S.submitGrade(t1.id, w1);
const dump = S.exportJSON();
S.reset();
ok('重置后清空', S.stats().testCount === 0);
S.importJSON(dump);
ok('导入后恢复', S.stats().testCount === 1 && S.stats().totalWrong === 3, JSON.stringify(S.stats()));
ok('导入后统计一致', S.blindSpots().length === blindAfter.length);

console.log('\n' + pass + ' passed, ' + fail + ' failed\n');
process.exit(fail ? 1 : 0);
