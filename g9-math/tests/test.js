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
/* 82 个上游九年级点 + 8 个为北师大版补的点
   （九上：特殊四边形综合、中点四边形、黄金分割、相似与四边形综合；
     九下：圆的综合、隐圆最值、反比例与几何综合、解直角三角形建模） */
ok('初三本体 = 90（82 上游 + 8 北师大新增）',
  D.topics.filter(t => t.isCore).length === 90,
  D.topics.filter(t => t.isCore).length);
ok('先修边 = meta.depCount', D.deps.length === D.meta.depCount,
  D.deps.length + ' vs ' + D.meta.depCount);
ok('先修边 >= 664（上游 2026-10-22 版）', D.deps.length >= 664, D.deps.length);
ok('没有物理/英语点混入',
  D.topics.every(t => !/^cn[pe]_/.test(t.id)),
  D.topics.filter(t => /^cn[pe]_/.test(t.id)).map(t => t.id).slice(0, 5).join(','));
ok('每题都有解析', D.questions.every(q => q.explanation && q.explanation.length > 0));
ok('每题都有答案', D.questions.every(q => q.answer !== undefined && String(q.answer).length > 0));
/* 题干写了「如图」就必须真有图，否则孩子对着空气想象 */
const figMissing = D.questions.filter(q => /如图/.test(q.prompt) && !q.fig).map(q => q.id);
ok('题干说「如图」的题都配了图', figMissing.length === 0, figMissing.join(','));
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
/* isCore 是「沪科版九年级本体」；bnUnit 有值的点按北师大版也属于九上
   （特殊四边形在沪科版是八下），两种都算范围内 */
ok('全是九上范围内的知识点',
  paper.items.every(it => { const t = E.topic(it.topicId); return t.isCore || t.bnUnit; }));
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

console.log('\n== 北师大版九上（2026 新版） ==');

/* --- 提纲 --- */
const bn = E.bnChapters();
ok('北师大九上 = 6 章', bn.length === 6, bn.length);
const bnTitles = bn.map(c => c.title).join('/');
ok('章名与 2026 新版一致',
  bnTitles === '特殊平行四边形/一元二次方程/图形的相似/投影与视图/二次函数/概率的进一步认识',
  bnTitles);

const bnTopics = D.topics.filter(t => t.bnUnit);
ok('九上归位知识点 >= 45', bnTopics.length >= 45, bnTopics.length);
ok('meta.bnCount 自洽', D.meta.bnCount === bnTopics.length,
  D.meta.bnCount + ' vs ' + bnTopics.length);

/* 北师大九上第一章「特殊平行四边形」在沪科版里是八年级下，必须被归位进来 */
const rhombus = D.topics.filter(t => t.bnUnit === 1).map(t => t.name);
ok('第一章含菱形/矩形/正方形',
  rhombus.some(n => n.includes('菱形')) &&
  rhombus.some(n => n.includes('矩形')) &&
  rhombus.some(n => n.includes('正方形')),
  rhombus.join(','));

/* 反比例函数、圆、锐角三角函数在北师大版属于九下，不能算进九上 */
const outNames = D.topics.filter(t => t.bnOut).map(t => t.name).join(',');
ok('九上外排除反比例函数', outNames.includes('反比例函数'), outNames.slice(0, 40));
ok('九上外排除圆', outNames.includes('垂径定理') || outNames.includes('切线'));
ok('反比例函数不在九上范围内', !D.topics.some(t => t.bnUnit && t.name.includes('反比例')));

/* --- 小节编排：照 2026 秋教材原书目录，不是自己编的 ---
   核对来源：电子课本网《北师大版九年级数学上册(2026秋版)》目录页。
   新版用「1、2、3」分节，所以「1.2」= 第一章第 2 节，不是「第一章第 1 节第 2 小点」。 */
const SEC = {
  1: ['认识特殊平行四边形', '菱形的性质与判定', '矩形的性质与判定', '正方形的性质与判定',
      '问题解决活动：作内嵌于正方形的正八边形', '回顾与思考'],
  2: ['认识一元二次方程', '一元二次方程的解法', '一元二次方程的根与系数的关系',
      '一元二次方程的应用', '回顾与思考'],
  3: ['相似多边形', '探索三角形相似的条件', '相似三角形判定定理的证明', '相似三角形的性质',
      '图形的位似', '问题解决活动：利用相似三角形测高', '回顾与思考'],
  4: ['投影', '视图', '回顾与思考'],
  5: ['认识二次函数', '二次函数的图象', '二次函数的应用', '二次函数与一元二次方程',
      '问题解决活动：怎样围面积最大', '回顾与思考'],
  6: ['用树状图或表格求概率', '用频率估计概率', '回顾与思考']
};
let secBad = [];
bn.forEach(c => {
  const want = SEC[c.no] || [];
  const got = c.sections.map(s => s.title);
  if (got.join('|') !== want.join('|')) {
    secBad.push('第' + c.no + '章 期望[' + want.join('|') + '] 实际[' + got.join('|') + ']');
  }
});
ok('各章节名与教材目录逐条一致', secBad.length === 0, secBad.join(' / '));

let noBad = [];
bn.forEach(c => c.sections.forEach((s, i) => {
  if (s.no !== c.no + '.' + (i + 1)) noBad.push(s.no + ' ' + s.title);
}));
ok('小节号 = 章号.节序', noBad.length === 0, noBad.join(','));

/* 每个归位点都得挂在一个真实存在的小节上，否则卷子上会显示空标签 */
const secOf = {};
bn.forEach(c => c.sections.forEach(s => s.topics.forEach(id => { secOf[id] = s.no; })));
const lost = bnTopics.filter(t => !secOf[t.id]).map(t => t.id + ' ' + t.name);
ok('归位点都能在小节里找到', lost.length === 0, lost.join(','));

/* 关键归位的抽查：错了家长照着课本翻不到 */
const secName = id => {
  for (const c of bn) for (const s of c.sections) if (s.topics.includes(id)) return s.no + ' ' + s.title;
  return '?';
};
ok('菱形在第一章第 2 节', secName('cnm_189').startsWith('1.2 菱形'), secName('cnm_189'));
ok('矩形在第一章第 3 节', secName('cnm_186').startsWith('1.3 矩形'), secName('cnm_186'));
ok('正方形在第一章第 4 节', secName('cnm_191').startsWith('1.4 正方形'), secName('cnm_191'));
ok('二次函数与一元二次方程独立成节 5.4',
  secName('cnm_234').startsWith('5.4 二次函数与一元二次方程'), secName('cnm_234'));
ok('黄金分割归到 3.1 相似多边形', secName('bn_t03').startsWith('3.1 相似多边形'), secName('bn_t03'));
ok('根与系数关系独立成节 2.3', secName('cnm_226').startsWith('2.3 一元二次方程的根'), secName('cnm_226'));

/* 标签：北师大档必须说北师大章节，不能退回「八年级」 */
const rhombusTopic = D.topics.find(t => t.id === 'cnm_189');
const lbl = E.bnLabel(rhombusTopic);
ok('bnLabel 给出北师大章节', lbl.indexOf('北师大九上') === 0 && lbl.includes('1.2'), lbl);
ok('bnLabel 不出现年级字样', !/年级/.test(lbl), lbl);
ok('bnLabel 对非九上点返回空', E.bnLabel(D.topics.find(t => !t.bnUnit)) === '');
ok('菱形在沪科版仍是八年级（标签只是换说法，数据没改）', rhombusTopic.grade === 8, rhombusTopic.grade);

/* --- 压轴题库 --- */
/* 九上这一节只数九上的题；九下那 33 道在下面单独算，别混进来 */
const zzQs = D.questions.filter(q => {
  const t = D.topics.find(x => x.id === q.topicId);
  return q.difficulty === 'zz' && t && t.bnUnit;
});
ok('九上压轴题 >= 30 道', zzQs.length >= 30, zzQs.length);
ok('meta.bnQuestionCount 自洽', D.meta.bnQuestionCount === zzQs.length,
  D.meta.bnQuestionCount + ' vs ' + zzQs.length);
ok('压轴题都挂在九上知识点下',
  zzQs.every(q => { const t = D.topics.find(x => x.id === q.topicId); return t && t.bnUnit; }));
ok('压轴题都有解析', zzQs.every(q => (q.explanation || '').length > 10));
ok('解答题有分值和书写空间',
  zzQs.filter(q => q.type === 'short').every(q => q.points > 0 && q.space > 0));

/* --- 出卷 --- */
function bnPaper(seed) {
  return E.generatePaper({
    tier: 'bn', count: 24, shortCount: 8, choiceQuota: 10,
    ratio: { basic: 0, standard: 0, advanced: 0, zz: 1 },
    hardMode: true, mode: 'normal', seed: seed
  });
}
[20261021, 7, 12345, 999999].forEach(seed => {
  const p = bnPaper(seed);
  const qs = p.items.map(it => D.questions.find(q => q.id === it.qid));
  const nChoice = qs.filter(q => q.type === 'choice').length;
  const nNum = qs.filter(q => q.type === 'numeric').length;
  const nShort = qs.filter(q => q.type === 'short').length;
  ok('seed ' + seed + ' 出满 24 题', p.count === 24, p.count);
  ok('seed ' + seed + ' 全部是压轴题', qs.every(q => q.difficulty === 'zz'),
    qs.filter(q => q.difficulty !== 'zz').length + ' 道不是');
  ok('seed ' + seed + ' 卷面 10 选择 + 6 填空 + 8 解答',
    nChoice === 10 && nNum === 6 && nShort === 8,
    nChoice + '/' + nNum + '/' + nShort);
  const ids = p.items.map(it => it.qid);
  ok('seed ' + seed + ' 没有重复题', new Set(ids).size === ids.length,
    ids.length - new Set(ids).size);
  ok('seed ' + seed + ' 题目都在九上六章内',
    qs.every(q => { const t = D.topics.find(x => x.id === q.topicId); return t && t.bnUnit; }));
});

/* 卷面分值：和青岛这套周测卷对齐，10×3 + 6×3 + 72 = 120 */
[20261021, 7, 12345, 999999].forEach(seed => {
  const p = bnPaper(seed);
  const sum = t => p.items.filter(it => it.type === t)
    .reduce((a, it) => a + it.points, 0);
  ok('seed ' + seed + ' 满分 120', sum('choice') + sum('numeric') + sum('short') === 120,
    sum('choice') + '+' + sum('numeric') + '+' + sum('short'));
  ok('seed ' + seed + ' 选择 30 分 / 填空 18 分',
    sum('choice') === 30 && sum('numeric') === 18, sum('choice') + '/' + sum('numeric'));
  const sp = p.items.filter(it => it.type === 'short').map(it => it.points);
  ok('seed ' + seed + ' 解答题分值是偶数分', sp.every(v => v % 2 === 0), sp.join(','));
  ok('seed ' + seed + ' 每道题都有分值', p.items.every(it => it.points > 0),
    p.items.filter(it => !it.points).length + ' 道没分');
});

console.log('\n== 北师大版九下（2024 新版） ==');

/* --- 提纲 ---
   九下 2026 秋版还没出版，按北师大 2024 版九下目录核对：
   三章 + 两个综合与实践（制作遮阳篷模型 / 制作视力表）。 */
const bn2 = E.bn2Chapters();
ok('北师大九下 = 3 章', bn2.length === 3, bn2.length);
const bn2Titles = bn2.map(c => c.title).join('/');
ok('九下章名与 2024 新版一致',
  bn2Titles === '直角三角形的边角关系/反比例函数/圆', bn2Titles);

const SEC2 = {
  1: ['锐角三角函数', '解直角三角形', '三角函数的应用', '回顾与思考'],
  2: ['认识反比例函数', '反比例函数的图象', '反比例函数的应用', '回顾与思考'],
  3: ['圆的有关性质', '确定圆的条件', '直线和圆的位置关系', '圆内接正多边形',
      '弧长及扇形的面积', '回顾与思考']
};
let sec2Bad = [];
bn2.forEach(c => {
  const want = SEC2[c.no] || [];
  const got = c.sections.map(s => s.title);
  if (got.join('|') !== want.join('|')) {
    sec2Bad.push('第' + c.no + '章 期望[' + want.join('|') + '] 实际[' + got.join('|') + ']');
  }
});
ok('九下各章节名与教材目录逐条一致', sec2Bad.length === 0, sec2Bad.join(' / '));

let no2Bad = [];
bn2.forEach(c => c.sections.forEach((s, i) => {
  if (s.no !== c.no + '.' + (i + 1)) no2Bad.push(s.no + ' ' + s.title);
}));
ok('九下小节号 = 章号.节序', no2Bad.length === 0, no2Bad.join(','));

const bn2Topics = D.topics.filter(t => t.bn2Unit);
ok('九下归位知识点 >= 30', bn2Topics.length >= 30, bn2Topics.length);
ok('meta.bn2Count 自洽', D.meta.bn2Count === bn2Topics.length,
  D.meta.bn2Count + ' vs ' + bn2Topics.length);
ok('九上九下没有点被同时归位', D.topics.every(t => !(t.bnUnit && t.bn2Unit)),
  D.topics.filter(t => t.bnUnit && t.bn2Unit).map(t => t.id).join(','));

const sec2Of = {};
bn2.forEach(c => c.sections.forEach(s => s.topics.forEach(id => { sec2Of[id] = s.no; })));
const lost2 = bn2Topics.filter(t => !sec2Of[t.id]).map(t => t.id + ' ' + t.name);
ok('九下归位点都能在小节里找到', lost2.length === 0, lost2.join(','));

const sec2Name = id => {
  for (const c of bn2) for (const s of c.sections) if (s.topics.includes(id)) return s.no + ' ' + s.title;
  return '?';
};
ok('锐角三角函数在 1.1', sec2Name('cnm_276').startsWith('1.1 锐角三角函数'), sec2Name('cnm_276'));
ok('解直角三角形在 1.2', sec2Name('cnm_278').startsWith('1.2 解直角三角形'), sec2Name('cnm_278'));
ok('认识反比例函数在 2.1', sec2Name('cnm_237').startsWith('2.1 认识反比例函数'), sec2Name('cnm_237'));
ok('反比例图象在 2.2', sec2Name('cnm_238').startsWith('2.2 反比例函数的图象'), sec2Name('cnm_238'));
ok('圆的有关性质在 3.1', sec2Name('cnm_250').startsWith('3.1 圆的有关性质'), sec2Name('cnm_250'));
ok('切线在 3.3 直线和圆的位置关系',
  sec2Name('cnm_260').startsWith('3.3 直线和圆的位置关系'), sec2Name('cnm_260'));
ok('弧长与扇形面积在 3.5', sec2Name('cnm_256').startsWith('3.5 弧长及扇形的面积'), sec2Name('cnm_256'));

/* 九下的点必须真的在九下：反比例、圆、锐角三角函数 */
ok('九下含反比例函数', bn2Topics.some(t => t.name.includes('反比例')));
ok('九下含圆', bn2Topics.some(t => t.name.includes('垂径定理') || t.name.includes('切线')));
ok('九下含锐角三角函数', bn2Topics.some(t => t.name.includes('锐角三角函数') || t.name.includes('正弦')));

/* 标签：九下必须说「北师大九下」，不能说成九上 */
const invTopic = D.topics.find(t => t.id === 'cnm_237');
const lbl2 = E.bnLabel(invTopic, 'bn2');
ok('bnLabel 九下分支给出北师大九下', lbl2.indexOf('北师大九下') === 0 && lbl2.includes('2.1'), lbl2);
ok('bnLabel 九下不出现年级字样', !/年级/.test(lbl2), lbl2);
ok('bnLabel 九下点按九上取会返回空', E.bnLabel(invTopic) === '');

/* --- 压轴题库 --- */
const zz2Qs = D.questions.filter(q => {
  const t = D.topics.find(x => x.id === q.topicId);
  return q.difficulty === 'zz' && t && t.bn2Unit;
});
ok('九下压轴题 >= 30 道', zz2Qs.length >= 30, zz2Qs.length);
ok('meta.bn2QuestionCount 自洽', D.meta.bn2QuestionCount === zz2Qs.length,
  D.meta.bn2QuestionCount + ' vs ' + zz2Qs.length);
ok('九下压轴题都挂在九下知识点下',
  zz2Qs.every(q => { const t = D.topics.find(x => x.id === q.topicId); return t && t.bn2Unit && !t.bnUnit; }));
ok('九下压轴题都有解析', zz2Qs.every(q => (q.explanation || '').length > 10));
ok('九下解答题有分值和书写空间',
  zz2Qs.filter(q => q.type === 'short').every(q => q.points > 0 && q.space > 0));

/* --- 出卷 --- */
function bn2Paper(seed) {
  return E.generatePaper({
    tier: 'bn2', count: 24, shortCount: 8, choiceQuota: 10,
    ratio: { basic: 0, standard: 0, advanced: 0, zz: 1 },
    hardMode: true, mode: 'normal', seed: seed
  });
}
[20261021, 7, 12345, 999999].forEach(seed => {
  const p = bn2Paper(seed);
  const qs = p.items.map(it => D.questions.find(q => q.id === it.qid));
  const nChoice = qs.filter(q => q.type === 'choice').length;
  const nNum = qs.filter(q => q.type === 'numeric').length;
  const nShort = qs.filter(q => q.type === 'short').length;
  ok('九下 seed ' + seed + ' 出满 24 题', p.count === 24, p.count);
  ok('九下 seed ' + seed + ' 全部是压轴题', qs.every(q => q.difficulty === 'zz'),
    qs.filter(q => q.difficulty !== 'zz').length + ' 道不是');
  ok('九下 seed ' + seed + ' 卷面 10 选择 + 6 填空 + 8 解答',
    nChoice === 10 && nNum === 6 && nShort === 8,
    nChoice + '/' + nNum + '/' + nShort);
  const ids = p.items.map(it => it.qid);
  ok('九下 seed ' + seed + ' 没有重复题', new Set(ids).size === ids.length,
    ids.length - new Set(ids).size);
  ok('九下 seed ' + seed + ' 题目都在九下三章内',
    qs.every(q => { const t = D.topics.find(x => x.id === q.topicId); return t && t.bn2Unit; }));

  const sum = t => p.items.filter(it => it.type === t).reduce((a, it) => a + it.points, 0);
  ok('九下 seed ' + seed + ' 满分 120',
    sum('choice') + sum('numeric') + sum('short') === 120,
    sum('choice') + '+' + sum('numeric') + '+' + sum('short'));
  ok('九下 seed ' + seed + ' 选择 30 分 / 填空 18 分',
    sum('choice') === 30 && sum('numeric') === 18, sum('choice') + '/' + sum('numeric'));
  ok('九下 seed ' + seed + ' 解答题分值是偶数分',
    p.items.filter(it => it.type === 'short').every(it => it.points % 2 === 0),
    p.items.filter(it => it.type === 'short').map(it => it.points).join(','));
});

/* --- 三档互不污染 --- */
[20261021, 7, 12345].forEach(seed => {
  const up = bnPaper(seed);
  ok('九上 seed ' + seed + ' 不掺九下的题',
    up.items.every(it => { const t = D.topics.find(x => x.id === it.topicId); return t.bnUnit && !t.bn2Unit; }),
    up.items.filter(it => { const t = D.topics.find(x => x.id === it.topicId); return !t.bnUnit; })
      .map(it => it.qid).join(','));

  const down = bn2Paper(seed);
  ok('九下 seed ' + seed + ' 不掺九上的题',
    down.items.every(it => { const t = D.topics.find(x => x.id === it.topicId); return t.bn2Unit && !t.bnUnit; }),
    down.items.filter(it => { const t = D.topics.find(x => x.id === it.topicId); return !t.bn2Unit; })
      .map(it => it.qid).join(','));

  const norm = E.generatePaper({ count: 25, shortCount: 5, mode: 'normal', seed: seed });
  ok('普通 seed ' + seed + ' 不掺压轴题',
    norm.items.every(it => D.questions.find(q => q.id === it.qid).difficulty !== 'zz'));
});

/* 按章筛选：只勾九下第三章「圆」，出的题必须全在圆 */
const onlyCircle = E.generatePaper({
  tier: 'bn2', bnUnits: [3], count: 24, shortCount: 8, choiceQuota: 10,
  mode: 'normal', seed: 20261021
});
ok('九下按章筛选只出第三章',
  onlyCircle.items.length > 0 &&
  onlyCircle.items.every(it => D.topics.find(x => x.id === it.topicId).bn2Unit === 3),
  onlyCircle.items.filter(it => D.topics.find(x => x.id === it.topicId).bn2Unit !== 3).length + ' 道越界');

/* coreTopics 要认九下的点，否则先修链、诊断会漏 */
ok('coreTopics 含九下归位点',
  E.coreTopics().filter(t => t.bn2Unit).length === bn2Topics.length,
  E.coreTopics().filter(t => t.bn2Unit).length + ' vs ' + bn2Topics.length);
ok('bnTopics 按九下取数', E.bnTopics(null, 'bn2').length === bn2Topics.length,
  E.bnTopics(null, 'bn2').length);

/* 普通卷也要有分值，否则卷头「共 X 分」是空的 */
const normalP = E.generatePaper({ count: 20, shortCount: 4, mode: 'normal', seed: 7 });
ok('普通卷客观题有默认分值',
  normalP.items.filter(it => it.type === 'choice' || it.type === 'numeric')
    .every(it => it.points > 0));

/* 普通卷不能掺压轴题，否则难度失控 */
[20261021, 7, 12345].forEach(seed => {
  const p = E.generatePaper({ count: 25, shortCount: 5, mode: 'normal', seed: seed });
  const qs = p.items.map(it => D.questions.find(q => q.id === it.qid));
  ok('seed ' + seed + ' 普通卷不含压轴题',
    qs.every(q => q.difficulty !== 'zz'),
    qs.filter(q => q.difficulty === 'zz').length + ' 道混入');
});

console.log('\n' + pass + ' passed, ' + fail + ' failed\n');
process.exit(fail ? 1 : 0);
