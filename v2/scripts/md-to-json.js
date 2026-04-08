/**
 * md-to-json.js
 * 将 2018Intl.md 转换为 JSON 格式题库
 *
 * 用法: node md-to-json.js
 */

const fs = require('fs');
const path = require('path');

// 读取 md 文件
const mdPath = 'C:/Users/25472/Desktop/AP/真题/calculus-bc/2018Intl.md';
const mdContent = fs.readFileSync(mdPath, 'utf8');

// 解析答案
function parseAnswerKey(md) {
  const answers = {};
  const answerRegex = /Question (\d+):\s*([A-D])/g;
  let match;
  while ((match = answerRegex.exec(md)) !== null) {
    answers[parseInt(match[1])] = match[2];
  }
  return answers;
}

// 解析题目
function parseQuestions(md, answers) {
  const questions = [];

  // 分割各部分
  // Part A: 题号 1-30, 无计算器
  // Part B: 题号 31-45, 有计算器

  // 找所有题目 - 使用正则匹配题号
  // 题目格式: ^数字+. $ 或 ^\d+\. $
  const lines = md.split('\n');
  let currentQuestion = null;
  let currentSection = 'mcq-1'; // Part A
  let inAnswerKey = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // 跳过答案部分
    if (line.includes('Multiple-Choice Answer Key') || line.includes('Answer Key for')) {
      inAnswerKey = true;
      continue;
    }
    if (inAnswerKey) continue;

    // 检测 Part 切换
    if (line.includes('SECTION I, Part B') || line.includes('PART B STARTS')) {
      currentSection = 'mcq-2';
      continue;
    }
    if (line.includes('SECTION II')) {
      break; // 跳过 FRQ
    }

    // 跳过非题目行
    if (!line || line.match(/^[A-Z\s]+$/) || line.startsWith('\\') || line.startsWith('#')) {
      if (currentQuestion && line.match(/^\([A-D]\)/)) {
        // 这是选项行
        const optionMatch = line.match(/^\(([A-D])\)\s*(.+)$/);
        if (optionMatch) {
          currentQuestion.options.push({
            key: optionMatch[1],
            html: optionMatch[2].trim()
          });
        }
      }
      continue;
    }

    // 题号行
    const qMatch = line.match(/^(\d+)\.\s*(.+)$/);
    if (qMatch) {
      if (currentQuestion) {
        questions.push(currentQuestion);
      }

      const qNum = parseInt(qMatch[1]);
      const sectionId = qNum <= 30 ? 'mcq-1' : 'mcq-2';

      currentQuestion = {
        question_id: `q${qNum}`,
        exam_id: 'calc-bc-2018-intl',
        section_id: sectionId,
        sequence_in_exam: qNum,
        question_type: 'single_choice',
        question_html: qMatch[2].trim(),
        options: [],
        correct_answer: answers[qNum] || '',
        unit: ''
      };
    } else if (currentQuestion && line.match(/^\([A-D]\)/)) {
      // 选项行
      const optionMatch = line.match(/^\(([A-D])\)\s*(.+)$/);
      if (optionMatch) {
        currentQuestion.options.push({
          key: optionMatch[1],
          html: optionMatch[2].trim()
        });
      }
    }
  }

  if (currentQuestion) {
    questions.push(currentQuestion);
  }

  return questions;
}

// 主函数
function main() {
  console.log('开始转换 2018Intl.md...\n');

  // 解析答案
  const answers = parseAnswerKey(mdContent);
  console.log(`找到 ${Object.keys(answers).length} 个答案`);

  // 解析题目
  const questions = parseQuestions(mdContent, answers);
  console.log(`找到 ${questions.length} 道题目\n`);

  // 输出 JSON
  const outputDir = path.join(__dirname, '..', 'data', 'calc-bc-2018-intl');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 保存所有题目为一个 JSON 文件
  const questionsFile = path.join(outputDir, 'questions.json');
  fs.writeFileSync(questionsFile, JSON.stringify(questions, null, 2), 'utf8');
  console.log(`已保存题目: ${questionsFile}`);

  // 创建 exam_packet.json
  const examPacket = {
    exam_id: 'calc-bc-2018-intl',
    exam_title: 'AP Calculus BC 2018 国际卷',
    subject: 'calculus_bc',
    subject_display: '微积分BC',
    year: 2018,
    form: 'international',
    total_questions: questions.length,
    sections: [
      {
        section_id: 'mcq-1',
        section_type: 'mcq',
        part_label: 'Part A',
        time_limit_minutes: 60,
        calculator_allowed: false,
        question_count: 30
      },
      {
        section_id: 'mcq-2',
        section_type: 'mcq',
        part_label: 'Part B',
        time_limit_minutes: 45,
        calculator_allowed: true,
        question_count: 15
      }
    ],
    metadata: {
      source: '2018Intl.md',
      converted_at: new Date().toISOString().split('T')[0],
      language: 'en'
    }
  };

  const packetFile = path.join(outputDir, 'exam_packet.json');
  fs.writeFileSync(packetFile, JSON.stringify(examPacket, null, 2), 'utf8');
  console.log(`已保存考试包: ${packetFile}`);

  // 创建 exams/index.json
  const indexDir = path.join(__dirname, '..', 'data', 'exams');
  if (!fs.existsSync(indexDir)) {
    fs.mkdirSync(indexDir, { recursive: true });
  }
  const indexFile = path.join(indexDir, 'index.json');
  fs.writeFileSync(indexFile, JSON.stringify([examPacket], null, 2), 'utf8');
  console.log(`已保存索引: ${indexFile}`);

  console.log('\n转换完成！');
  console.log(`\n题目预览 (前3题):`);
  questions.slice(0, 3).forEach(q => {
    console.log(`\n${q.question_id}: ${q.question_html.substring(0, 60)}...`);
    console.log(`  答案: ${q.correct_answer}`);
    console.log(`  选项数: ${q.options.length}`);
  });
}

main();
