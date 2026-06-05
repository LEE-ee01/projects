const {
  Document, Paragraph, TextRun, HeadingLevel,
  AlignmentType, TabStopType, TabStopPosition,
  BorderStyle, WidthType, Packer,
  Table, TableRow, TableCell, TableWidthType,
  ShadingType, convertInchesToTwip
} = require('docx');
const fs = require('fs');

// Shared styles
const FONT = 'Microsoft YaHei';
const FONT_EN = 'Arial';
const BODY_SIZE = 21; // 10.5pt in half-points
const HEADER_SIZE = 28; // 14pt
const NAME_SIZE = 36; // 18pt
const SMALL_SIZE = 20; // 10pt
const MARGIN = convertInchesToTwip(0.8);

// Helper functions
function bodyText(text, opts = {}) {
  return new TextRun({
    text,
    font: { name: FONT_EN, eastAsia: FONT },
    size: opts.size || BODY_SIZE,
    bold: opts.bold || false,
    color: opts.color || '333333',
    ...opts,
  });
}

function sectionHeader(text) {
  return new Paragraph({
    spacing: { before: 260, after: 80 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 1, color: '2B579A' },
    },
    children: [
      new TextRun({
        text,
        font: { name: FONT_EN, eastAsia: FONT },
        size: HEADER_SIZE,
        bold: true,
        color: '2B579A',
      }),
    ],
  });
}

function bullet(text, runs = []) {
  return new Paragraph({
    spacing: { after: 40, line: 276 }, // 1.15 line spacing
    bullet: { level: 0 },
    children: [
      ...runs,
      new TextRun({
        text,
        font: { name: FONT_EN, eastAsia: FONT },
        size: BODY_SIZE,
        color: '333333',
      }),
    ],
  });
}

function simpleLine(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after || 40, line: 276 },
    children: [
      new TextRun({
        text,
        font: { name: FONT_EN, eastAsia: FONT },
        size: opts.size || BODY_SIZE,
        bold: opts.bold || false,
        color: opts.color || '333333',
      }),
      ...(opts.runs || []),
    ],
  });
}

function boldBullet(boldPart, normalPart) {
  return new Paragraph({
    spacing: { after: 40, line: 276 },
    bullet: { level: 0 },
    children: [
      new TextRun({
        text: boldPart,
        font: { name: FONT_EN, eastAsia: FONT },
        size: BODY_SIZE,
        bold: true,
        color: '333333',
      }),
      new TextRun({
        text: normalPart,
        font: { name: FONT_EN, eastAsia: FONT },
        size: BODY_SIZE,
        color: '333333',
      }),
    ],
  });
}

// Create document
const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: { name: FONT_EN, eastAsia: FONT },
          size: BODY_SIZE,
          color: '333333',
        },
      },
    },
  },
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: MARGIN,
            bottom: MARGIN,
            left: convertInchesToTwip(0.85),
            right: convertInchesToTwip(0.85),
          },
        },
      },
      children: [
        // ===== NAME =====
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: '李欣昱',
              font: { name: FONT_EN, eastAsia: FONT },
              size: NAME_SIZE,
              bold: true,
              color: '1A1A1A',
            }),
          ],
        }),

        // ===== CONTACT INFO =====
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 80 },
          children: [
            new TextRun({
              text: '📞 181-8730-4850  |  ✉️ lixinyu12133@gmail.com  |  🔗 github.com/LEE-ee01  |  📍 湖南 · 长沙',
              font: { name: FONT_EN, eastAsia: FONT },
              size: SMALL_SIZE,
              color: '555555',
            }),
          ],
        }),

        // ===== 求职意向 =====
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 40 },
          children: [
            new TextRun({
              text: '求职意向：数据分析（实习）',
              font: { name: FONT_EN, eastAsia: FONT },
              size: 23,
              bold: true,
              color: '2B579A',
            }),
          ],
        }),

        // ===== 教育背景 =====
        sectionHeader('教育背景 / Education'),

        new Paragraph({
          spacing: { before: 60, after: 30, line: 276 },
          children: [
            new TextRun({
              text: '中南大学',
              font: { name: FONT_EN, eastAsia: FONT },
              size: BODY_SIZE,
              bold: true,
              color: '333333',
            }),
            new TextRun({
              text: '  |  信息管理与信息系统  |  本科  |  CET-4：521',
              font: { name: FONT_EN, eastAsia: FONT },
              size: BODY_SIZE,
              color: '555555',
            }),
          ],
        }),
        new Paragraph({
          spacing: { after: 40, line: 276 },
          children: [
            new TextRun({
              text: '2023.09 - 2027.06（预计）',
              font: { name: FONT_EN, eastAsia: FONT },
              size: SMALL_SIZE,
              color: '777777',
            }),
          ],
        }),

        simpleLine('主修课程：', {
          bold: true,
          after: 30,
          runs: [
            new TextRun({
              text: '机器学习，大数据分析，数据爬取，智能推荐系统，数据库原理与应用，概率论与数理统计，线性代数，数据结构，管理信息系统，Web 开发技术',
              font: { name: FONT_EN, eastAsia: FONT },
              size: SMALL_SIZE,
              bold: false,
              color: '555555',
            }),
          ],
        }),

        // ===== 专业技能 =====
        sectionHeader('专业技能 / Skills'),

        // Skill table
        ...buildSkillsTable(),

        // ===== 项目经历 =====
        sectionHeader('项目经历 / Project Experience'),

        // Project 1
        projectHeader('基于 BERT 与多模态特征融合的电商评论水军检测系统'),
        projectSubtitle('独立完成  |  Python · BERT · XGBoost · Stacking · Pandas'),
        bullet('清洗 ', [
          new TextRun({ text: '3.8 万条', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, bold: true, color: '333333' }),
          new TextRun({ text: '中文电商评论数据，构建可解释性水军检测框架', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, color: '333333' }),
        ]),
        bullet('引入 BERT 预训练模型提取 ', [
          new TextRun({ text: '384 维', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, bold: true, color: '333333' }),
          new TextRun({ text: '语义向量，融合图网络与行为特征构建 ', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, color: '333333' }),
          new TextRun({ text: '410 维', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, bold: true, color: '333333' }),
          new TextRun({ text: '特征体系，解决短文本语义稀疏问题', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, color: '333333' }),
        ]),
        bullet('针对 ', [
          new TextRun({ text: '1:6 极度不平衡', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, bold: true, color: '333333' }),
          new TextRun({ text: '样本，采用 ADASYN 自适应过采样与动态阈值优化策略', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, color: '333333' }),
        ]),
        boldBullet('最终 F1 分数达 0.84，较基线模型提升 59%'),

        // Project 2
        projectHeader('仿 GnuCash 财务管理系统（Spring Boot + Vue）'),
        projectSubtitle('独立全栈开发  |  Java · Spring Boot · MySQL · MyBatis · Vue'),
        bullet('设计并实现前后端分离的复式记账财务系统'),
        bullet('利用 MyBatis 动态 SQL 实现 ', [
          new TextRun({ text: '多维度财务报表统计', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, bold: true, color: '333333' }),
          new TextRun({ text: '，支持按科目、期间、账套灵活汇总与可视化', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, color: '333333' }),
        ]),
        bullet('采用组合设计模式解决会计科目无限层级嵌套的树形结构问题'),
        bullet('核心功能：多账套管理、复式记账引擎、可视化报表'),

        // Project 3
        projectHeader('大学生创新创业项目 — 红色文化体验基地平台'),
        projectSubtitle('项目负责人  |  Vue · Spring Boot  |  校级立项'),
        bullet('带领团队打造结合云南红色文化与彝族文化资源的沉浸式体验平台'),
        bullet('面向党政机关、学校及游客提供主题教育、乡村体验及农产品营销一站式服务'),
        bullet('负责需求分析、技术选型与前后端开发协调'),

        // ===== 荣誉与证书 =====
        sectionHeader('荣誉与证书 / Honors & Certificates'),
        bullet('大学英语四级（CET-4）：', [
          new TextRun({ text: '521', font: { name: FONT_EN, eastAsia: FONT }, size: BODY_SIZE, bold: true, color: '333333' }),
        ]),
        bullet('大学生创新创业训练计划：校级立项（项目负责人）'),
      ],
    },
  ],
});

// Helper: project header
function projectHeader(text) {
  return new Paragraph({
    spacing: { before: 180, after: 30 },
    children: [
      new TextRun({
        text,
        font: { name: FONT_EN, eastAsia: FONT },
        size: 23,
        bold: true,
        color: '1A1A1A',
      }),
    ],
  });
}

// Helper: project subtitle
function projectSubtitle(text) {
  return new Paragraph({
    spacing: { after: 60 },
    children: [
      new TextRun({
        text,
        font: { name: FONT_EN, eastAsia: FONT },
        size: SMALL_SIZE,
        color: '888888',
      }),
    ],
  });
}

// Build skills table
function buildSkillsTable() {
  const skills = [
    { cat: '编程语言', items: 'Python（主力），Java，SQL' },
    { cat: '数据分析', items: 'Pandas，NumPy，MySQL，SQL Server' },
    { cat: '机器学习', items: 'BERT（Transformer），Sentence-Transformers，XGBoost，LightGBM，CatBoost，Random Forest，K-Means，Stacking 模型融合' },
    { cat: '后端与工具', items: 'Spring Boot，Spring MVC，MyBatis，Vue，Git' },
    { cat: '办公软件', items: 'Excel（数据透视表），PowerPoint，Word' },
  ];

  return skills.map(({ cat, items }) =>
    new Paragraph({
      spacing: { before: 40, after: 40, line: 276 },
      children: [
        new TextRun({
          text: `▎${cat}：`,
          font: { name: FONT_EN, eastAsia: FONT },
          size: BODY_SIZE,
          bold: true,
          color: '2B579A',
        }),
        new TextRun({
          text: items,
          font: { name: FONT_EN, eastAsia: FONT },
          size: BODY_SIZE,
          color: '555555',
        }),
      ],
    })
  );
}

// Generate and save
Packer.toBuffer(doc).then((buffer) => {
  const outputPath = 'C:/Users/lxy12/Desktop/cc/李欣昱_数据分析_简历.docx';
  fs.writeFileSync(outputPath, buffer);
  console.log('✅ 简历已生成: ' + outputPath);
});
