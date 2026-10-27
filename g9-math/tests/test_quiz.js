/* 线上判分 + 手机出卷的自测
 * 运行：node tests/test_quiz.js
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var ROOT = path.resolve(__dirname, '..');
var ctx = {
  console: console,
  Math: Math,
  Date: Date,
  JSON: JSON,
  Promise: Promise
};
ctx.globalThis = ctx;
ctx.window = ctx;
vm.createContext(ctx);

function run(rel) {
  var code = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  vm.runInContext(code, ctx, { filename: rel });
}

/* localStorage 模拟 */
ctx.localStorage = {
  _d: {},
  getItem: function (k) { return Object.prototype.hasOwnProperty.call(this._d, k) ? this._d[k] : null; },
  setItem: function (k, v) { this._d[k] = String(v); },
  removeItem: function (k) { delete this._d[k]; }
};

run('data/bundle.js');
run('assets/core.js');
run('assets/store.js');
run('assets/quizcore.js');

var Q = ctx.QuizCore;
var E = ctx.Engine;
var S = ctx.Store;

var pass = 0, fail = 0;
function ok(cond, name) {
  if (cond) { pass++; }
  else { fail++; console.log('  ✗ ' + name); }
}
function eq(a, b, name) { ok(a === b, name + '（实际 ' + JSON.stringify(a) + '，期望 ' + JSON.stringify(b) + '）'); }

console.log('== 填空题判分 ==');

eq(Q.checkNumeric('1,-5,6', '1，-5，6'), true, '半角逗号也能对');
eq(Q.checkNumeric('1，-5，6', '1，-5，6'), true, '全角逗号');
eq(Q.checkNumeric('-5, 1 , 6', '1，-5，6'), true, '顺序不同、带空格');
eq(Q.checkNumeric('0.5', '1/2'), true, '小数等于分数');
eq(Q.checkNumeric('1/2', '0.5'), true, '分数等于小数');
eq(Q.checkNumeric('-0.5', '-1/2'), true, '负分数');
eq(Q.checkNumeric('1/2', '-1/2'), false, '正负不同');
eq(Q.checkNumeric('2', '2'), true, '单值');
eq(Q.checkNumeric('2', '3'), false, '单值错');
eq(Q.checkNumeric('', '2'), false, '空答案');
eq(Q.checkNumeric('1,2', '1,2,3'), false, '少写一个');
eq(Q.checkNumeric('1,2,3', '1,2'), false, '多写一个');
eq(Q.checkNumeric('１，－５，６', '1，-5，6'), true, '全角数字和负号');
eq(Q.checkNumeric('x=2', '2'), true, '带 x= 前缀');
eq(Q.checkNumeric('2，2', '2，2'), true, '重复值');
eq(Q.checkNumeric('2，2', '2'), false, '重复值不匹配单值');
eq(Q.checkNumeric('0.3333333', '1/3'), false, '近似小数不算对（要求精确）');
eq(Q.checkNumeric('1/3', '1/3'), true, '分数精确');

console.log('== 选择题判分 ==');
eq(Q.checkChoice('B', 'B'), true, '选项相同');
eq(Q.checkChoice('b', 'B'), true, '小写也行');
eq(Q.checkChoice('A', 'B'), false, '选项不同');
eq(Q.checkChoice('', 'B'), false, '没选');

console.log('== 真实题目抽检 ==');

/* 出卷池 = 初三本体 + 北师大九上/九下的归位点。
   菱形、矩形这些在沪科版是八年级，但在北师大版是九年级正课，进卷是对的；
   七、八年级的纯先修点（小学的更是）不能进。 */
var core = E.coreTopics().map(function (t) { return t.id; });
var nums = E.data.questions.filter(function (q) {
  return q.type === 'numeric' && core.indexOf(q.topicId) !== -1;
});
var selfOk = 0;
nums.forEach(function (q) {
  if (Q.checkNumeric(q.answer, q.answer)) selfOk++;
});
eq(selfOk, nums.length, '标准答案自己判自己全对（' + nums.length + ' 题）');

/* 把逗号换成中文顿号、加点空格，仍应判对 */
var tolerant = nums.filter(function (q) {
  var messy = String(q.answer).replace(/，/g, ' ， ');
  return Q.checkNumeric(messy, q.answer);
}).length;
eq(tolerant, nums.length, '答案加空格后仍判对');

console.log('== 手机出卷 ==');

function makePaper(count) {
  var blind = S.blindSpots();
  var focus = blind.filter(function (b) { return b.isCore; }).map(function (b) { return b.topicId; });
  return E.generatePaper({
    scope: { semesters: ['上', '下'] },
    count: count,
    shortCount: 0,
    ratio: { basic: 0.2, standard: 0.45, advanced: 0.35 },
    hardMode: true,
    mode: 'normal',
    focus: focus,
    probe: [],
    usedQids: S.state.usedQids,
    topicStats: S.state.topicStats,
    seed: 12345
  });
}

var p = makePaper(12);
ok(p.count === 12, '12 题卷出满（实际 ' + p.count + '）');
var allObj = p.items.every(function (it) {
  var q = E.question(it.qid);
  return q && (q.type === 'choice' || q.type === 'numeric');
});
ok(allObj, '手机卷不含解答题');
var allCore = p.items.every(function (it) {
  return core.indexOf(it.topicId) !== -1;
});
ok(allCore, '手机卷只考正课范围（初三本体 + 北师大归位点）');
ok(p.items.every(function (it) {
  var t = E.topic(it.topicId);
  return t && t.grade >= 7;
}), '手机卷不掺七、八年级的纯先修题');

var types = {};
p.items.forEach(function (it) { types[E.question(it.qid).type] = 1; });
console.log('   题型分布：' + Object.keys(types).join(' + '));

/* 连出 5 张，模拟真实流程：每张做完后 usedQids 累积，下一张应避开旧题 */
var used = {};
var dupInSamePaper = 0;
var exhausted = 0;
for (var i = 0; i < 5; i++) {
  var pp = makePaper(16);
  var seen = {};
  pp.items.forEach(function (it) {
    if (seen[it.qid]) dupInSamePaper++;
    seen[it.qid] = 1;
    used[it.qid] = 1;
  });
  if (pp.count < 16) exhausted++;
  /* 关键：把这批题记进已用，模拟 Store.recomputeStats 的效果 */
  S.state.usedQids = Object.assign({}, used);
}
eq(dupInSamePaper, 0, '同一张卷不重复出题');
eq(exhausted, 0, '5 张 16 题卷都能出满');
ok(Object.keys(used).length >= 60,
  '5 张 16 题卷共用到 ' + Object.keys(used).length + ' 道不同题（去重生效）');

console.log('\n== 题图 ==');
(function () {
  var figs = E.data.questions.filter(function (q) { return q.fig; });
  ok(figs.length > 0, '题库里有 ' + figs.length + ' 道带图题');

  var badSvg = figs.filter(function (q) {
    return q.fig.indexOf('<svg') !== 0 || q.fig.indexOf('viewBox=') === -1;
  });
  eq(badSvg.length, 0, '每张题图都是带 viewBox 的 <svg>');

  /* SVG 里出现裸的 < 或未闭合标签，浏览器会整块吞掉，必须挡在数据层 */
  var broken = figs.filter(function (q) {
    return /<script|onload=|javascript:/i.test(q.fig);
  });
  eq(broken.length, 0, '题图里没有脚本或事件属性');

  /* 客观题也可以带图（圆、坡度、函数图象这类确实需要），解答题基本都有 */
  var byType = {};
  figs.forEach(function (q) { byType[q.type] = (byType[q.type] || 0) + 1; });
  ok(byType.short > 0, '解答题带图 ' + (byType.short || 0) + ' 道');
  ok((byType.choice || 0) + (byType.numeric || 0) > 0,
    '客观题带图 ' + ((byType.choice || 0) + (byType.numeric || 0)) + ' 道');

  var noAns = figs.filter(function (q) {
    return !q.answer || !q.explanation;
  });
  eq(noAns.length, 0, '带图题都还有答案和解析');
})();

console.log('\n' + (fail ? '✗ ' : '✓ ') + pass + ' 通过 / ' + fail + ' 失败');
process.exit(fail ? 1 : 0);
