/**
 * 答辩模拟角色配置
 * 包含不同性格的导师、趣味梗、真实场景对话等
 */

export type AdvisorPersonality = 'strict' | 'gentle' | 'humorous' | 'philosophical' | 'techGeek' | 'detailOriented' | 'encouraging'

export interface AdvisorCharacter {
  id: string
  name: string
  title: string
  avatar: string
  personality: AdvisorPersonality
  description: string
  speakingStyle: {
    greeting: string[]
    praise: string[]
    criticism: string[]
    questions: string[]
    followUp: string[]
    concluding: string[]
  }
  catchphrases: string[]
  memes: string[]
  questionStyle: 'sharp' | 'guiding' | 'socratic' | 'technical' | 'bigPicture'
  difficulty: 1 | 2 | 3 | 4 | 5
  focusAreas: string[]
}

export const advisorCharacters: AdvisorCharacter[] = [
  {
    id: 'professor_strict',
    name: '严教授',
    title: '资深博导',
    avatar: '🎓',
    personality: 'strict',
    description: '学术严谨，要求极高，被学生们称为"学术质检员"',
    speakingStyle: {
      greeting: [
        '我们开始吧，希望你做好了充分准备。',
        '时间有限，我直接看核心内容。',
        '不要紧张，但也不要期望我会放水。'
      ],
      praise: [
        '这部分做得不错，至少说明你认真读了文献。',
        '思路还算清晰，但还有很大提升空间。',
        '这个发现有点意思，值得继续深挖。'
      ],
      criticism: [
        '这个数据支撑明显不足，你确定能得出这个结论？',
        '第三章和第二章的逻辑断裂严重。',
        '这种表述在顶级期刊审稿人那里活不过三秒。',
        '你的创新点在哪里？我没看到令人眼前一亮的东西。'
      ],
      questions: [
        '如果评审人质疑你的样本量，你怎么回应？',
        '这个方法在2019年就已经被证明有缺陷了，你不知道吗？',
        '你的理论框架为什么选A而不是B？',
        '这个实验设计的controls在哪里？'
      ],
      followUp: [
        '这只是表面现象，深层机制呢？',
        '你还没回答我的问题，不要绕弯子。',
        '理论基础薄弱，再解释也没用。',
        '实证部分太单薄，需要更多的robustness checks。'
      ],
      concluding: [
        '总体来说达到了毕业要求，但离优秀还有距离。',
        '工作量够，但深度不够，回去继续打磨。',
        '勉强通过，但建议major revision后再提交。'
      ]
    },
    catchphrases: [
      '这个不行。',
      '重新做。',
      '逻辑呢？',
      '你的创新点在哪？',
      '这不够solid。'
    ],
    memes: [
      '【推眼镜.jpg】这个动作说明我要开始质疑了',
      '【扶额.jpg】经典的学生没读懂文献表情'
    ],
    questionStyle: 'sharp',
    difficulty: 5,
    focusAreas: ['方法论', '理论贡献', '实验设计', '文献综述']
  },
  {
    id: 'professor_humorous',
    name: '段教授',
    title: '段子手导师',
    avatar: '😄',
    personality: 'humorous',
    description: '学术界的脱口秀演员，用幽默化解紧张气氛，但点评一针见血',
    speakingStyle: {
      greeting: [
        '大家好，又到了一年一度的"学术版吐槽大会"。',
        '放松点，今天我不当大魔王，只是个好奇的观众。',
        '听说你论文写了十万字？内存条还好吗？'
      ],
      praise: [
        '这段写得可以，比我当年强多了（虽然这标准不高）。',
        '选题很勇啊，这个坑好多大佬都绕着走。',
        '实验数据这么漂亮，我都怀疑你是不是偷偷请外援了。',
        '这创新点，有当年我头发还在时的那股劲。'
      ],
      criticism: [
        '这个结论下的...梁静茹给你的勇气吗？',
        '第三章和第四章的关系，就像我和生发液的关系。',
        '样本量这么少，你是打算用玄学证明科学吗？',
        '这个文献综述...你该不会是用ChatGPT写的吧？（开玩笑的，别慌）'
      ],
      questions: [
        '如果评审说你这研究没啥用，你能忍住不哭吗？',
        '你的理论和实际之间，大概差了几个筋斗云？',
        '这个bug你修了吗？别告诉我你打算留给下届师弟。',
        '要是实验复现不了，你打算怪仪器、怪天气还是怪星座？'
      ],
      followUp: [
        '别急着解释，先让我笑会...',
        '这个锅甩得很有技巧，值得学习。',
        '你说的我都懂，但数据它自己同意吗？',
        '学术可以严肃，但咱们得实事求是对吧？'
      ],
      concluding: [
        '过了！今晚必须请客，我已经想好吃什么了。',
        '修改意见不多，就改到让我满意为止。',
        '恭喜你加入学术打工人行列，记得多买几包防脱洗发水。'
      ]
    },
    catchphrases: [
      '这个...很有想法（潜台词：很离谱）。',
      '我给你讲个笑话...',
      '不要方，问题不大。',
      '你这脑洞开得比我还大。',
      '学术界的段子手后继有人了。'
    ],
    memes: [
      '【狗头.jpg】保命必备',
      '【笑哭.jpg】哭笑不得的表情',
      '【扶额笑.jpg】被你气笑了'
    ],
    questionStyle: 'socratic',
    difficulty: 3,
    focusAreas: ['创新点', '实际应用', '可行性']
  },
  {
    id: 'professor_techGeek',
    name: '极客教授',
    title: '技术宅导师',
    avatar: '💻',
    personality: 'techGeek',
    description: '代码狂魔，对新技术如数家珍，能用脚本绝不用人工',
    speakingStyle: {
      greeting: [
        '请开始，我已经开好了Jupyter Notebook准备实时验证。',
        '希望你的代码比PPT漂亮。',
        '我们开始吧，我待会还有个模型要训练。'
      ],
      praise: [
        '这个算法优化得很漂亮，时间复杂度降了不少。',
        '可视化做得不错，matplotlib用到这个水平可以了。',
        'Git提交记录很规范，是个合格的开源贡献者了。',
        '这个自动化脚本写得666，节省了大量时间。'
      ],
      criticism: [
        '这段代码的时间复杂度是O(n²)，你确定能scale up？',
        '变量命名用拼音？这是要进《码农笑话大全》吗？',
        '没有单元测试？你这是裸奔啊。',
        '这模型过拟合得比我的头发还严重。',
        '数据清洗都没做？Garbage in, garbage out听说过吗？'
      ],
      questions: [
        '你的代码开源了吗？GitHub多少star？',
        '这个实验用Docker打包了吗？能一键复现吗？',
        '你的模型在M1芯片上能跑吗？',
        '数据备份了吗？服务器炸了怎么办？',
        '考虑过用Transformer吗？BERT不香吗？',
        '你用的包版本是多少？requirements.txt写了吗？'
      ],
      followUp: [
        '光说没用，run一下给我看看。',
        '这个bug复现不了，你环境没配对吧？',
        'benchmark呢？和SOTA比了吗？',
        '代码里这个magic number解释一下？'
      ],
      concluding: [
        'LGTM (Looks Good To Me)，merged！',
        '代码质量不错，accept with minor changes。',
        'CI/CD搞一搞就能发表了。'
      ]
    },
    catchphrases: [
      'Talk is cheap, show me the code.',
      '先跑起来再说。',
      'Ctrl+C, Ctrl+V了解一下？（开玩笑）',
      '这个可以用AI自动生成。',
      '上云了吗？容器化了吗？'
    ],
    memes: [
      '【Stack Overflow.jpg】程序员圣经',
      '【It Works.jpg】我不知道为什么，但它能跑',
      '【Bug Feature.jpg】这不是bug，是特性'
    ],
    questionStyle: 'technical',
    difficulty: 4,
    focusAreas: ['代码质量', '算法效率', '实验复现', '技术选型']
  },
  {
    id: 'professor_detail',
    name: '细教授',
    title: '细节控导师',
    avatar: '🔍',
    personality: 'detailOriented',
    description: '对格式、标点、引用要求极致，人称"学术处女座"',
    speakingStyle: {
      greeting: [
        '我先说一点：格式不规范的我不看内容。',
        '让我们从第1页开始，逐字逐句检查。',
        '希望你的论文经得起放大镜。'
      ],
      praise: [
        '格式很规范，参考文献排版完美。',
        '图表编号连续，没有跳号，好评。',
        '标点符号使用正确，这一点很多博士都做不到。',
        '页边距设置符合学校规范，用心了。'
      ],
      criticism: [
        '第三段第二行，逗号应该用中文逗号而不是英文逗号。',
        '图4.2和图4.3之间差了一个像素，对齐有问题。',
        '参考文献第23条，页码格式和其他不一致。',
        '公式编号右对齐偏离了0.5厘米，请修正。',
        '这个分号用的不对，前面是分句不是并列。',
        '致谢部分"的、地、得"用错了三处。'
      ],
      questions: [
        '你的行间距是1.5倍还是固定值20磅？',
        '参考文献的姓和名之间是逗号还是空格？',
        '这个单位是px还是pt？',
        '你的LaTeX模板是最新版吗？',
        '这个缩写第一次出现时全称写了吗？',
        '图表的caption是居中对齐吗？'
      ],
      followUp: [
        '这些问题看似小，但体现了学术态度。',
        '格式不规范，内容再好也白搭。',
        '细节决定成败，再检查一遍。',
        '这个错误太低级了，重写。'
      ],
      concluding: [
        '格式基本过关，回去再校对那些标点。',
        '内容不错，但格式问题太多，修改后再来。',
        '通过了，但你这强迫症程度还得加强。'
      ]
    },
    catchphrases: [
      '这里有个空格。',
      '对齐！对齐！对齐！',
      '标点符号不对。',
      '格式！格式！',
      '再检查一遍！'
    ],
    memes: [
      '【放大镜.jpg】每个像素都要对齐',
      '【红笔批改.jpg】满屏的红圈',
      '【格式检查器.jpg】自动检测格式错误'
    ],
    questionStyle: 'sharp',
    difficulty: 3,
    focusAreas: ['格式规范', '引用标准', '图表规范', '语言表达']
  }
]

// 趣味随机事件
export interface RandomEvent {
  id: string
  title: string
  description: string
  probability: number
  effect: 'positive' | 'negative' | 'neutral'
  advisorResponses: Record<AdvisorPersonality, string>
}

export const randomEvents: RandomEvent[] = [
  {
    id: 'ppt_crash',
    title: 'PPT崩溃事件',
    description: '答辩进行到一半，PPT突然打不开了！',
    probability: 0.05,
    effect: 'negative',
    advisorResponses: {
      strict: '这就是不提前测试的后果。继续，不要找借口。',
      gentle: '没关系，深呼吸，你可以直接讲的。',
      humorous: '哈哈，经典的"答辩必崩"定律应验了。脱稿讲吧，我相信你。',
      philosophical: '技术故障提醒我们：备份的哲学意义。',
      techGeek: '下次用PDF格式，PPT太不稳定了。我帮你看看？',
      detailOriented: '这也说明你没有提前测试设备，下次注意。',
      encouraging: '没关系！这是考验你应变能力的机会！你可以的！'
    }
  },
  {
    id: 'phone_rings',
    title: '手机铃声事件',
    description: '答辩过程中，你的手机突然响了，而且是最炫民族风...',
    probability: 0.1,
    effect: 'neutral',
    advisorResponses: {
      strict: '关掉它。下次记得静音。',
      gentle: '没关系，关掉就好，继续。',
      humorous: '品味不错，不过现在是学术时间。',
      philosophical: '现代性的侵扰无处不在。',
      techGeek: '你应该用forest App戒掉手机依赖。',
      detailOriented: '这是基本礼仪，下次请务必静音。',
      encouraging: '哈哈，活跃了气氛！继续吧！'
    }
  },
  {
    id: 'brilliant_answer',
    title: '灵光一闪',
    description: '你突然对一个难题给出了精彩的回答！',
    probability: 0.15,
    effect: 'positive',
    advisorResponses: {
      strict: '嗯，这个回答还算令人满意。',
      gentle: '非常漂亮！你的反应很快！',
      humorous: '哇哦！这波操作可以给满分！',
      philosophical: '这就是即兴思考的魅力。',
      techGeek: 'Nice! 这反应速度，可以写进缓存了。',
      detailOriented: '回答不错，但格式上还可以优化...',
      encouraging: '看到没！我就知道你能行！'
    }
  }
]

// 学术圈趣味梗
export const academicMemes = [
  '【你的头发还好吗？】学术圈的终极问候',
  '【 deadline 是第一生产力】不到最后一刻不开始',
  '【Reviewer 2】传说中最严厉的审稿人',
  '【我的代码能跑】至理名言，不要问为什么',
  '【 P 值小于 0.05】统计显著，但可能没意义',
  '【致谢里感谢猫咪】学术写作的传统美德',
  '【参考文献比正文长】文献综述的正确打开方式',
  '【这个领域太卷了】为什么我要选择这个方向...',
  '【老板又给我派活了】研究生日常',
  '【 coffee is my blood】学术人的续命神器'
]

// 答辩彩蛋
export const easterEggs = {
  specialDates: {
    '04-01': {
      title: '愚人节特别答辩',
      description: '今天所有导师都变成了段子手模式！',
      effect: '所有导师使用幽默语录'
    },
    '11-11': {
      title: '光棍节答辩',
      description: '答辩委员会都是单身狗，心情可能不太好...',
      effect: '难度+1'
    }
  },
  specialTriggers: [
    {
      condition: (stats: any) => stats.wordCount > 100000,
      title: '史诗级论文',
      description: '你的论文比《红楼梦》还长！',
      reward: '获得"卷王"称号'
    },
    {
      condition: (stats: any) => stats.citationCount === 0,
      title: '零引用勇士',
      description: '一篇参考文献都没有？你是原创之神吗？',
      reward: '触发"你是个狼人"彩蛋'
    },
    {
      condition: (stats: any) => stats.title.includes('基于'),
      title: '标题党',
      description: '基于...的研究，学术圈最安全的标题',
      reward: '导师会心一笑'
    }
  ]
}

// 答辩后评价模板
export const evaluationTemplates = {
  excellent: [
    '🌟 完美！你就是学术界的明日之星！',
    '🎓 太优秀了！建议直接申请教职！',
    '💯 无可挑剔，这就是标杆级的答辩！',
    '✨ 才华横溢，令人印象深刻！'
  ],
  good: [
    '👍 表现不错，达到了优秀水平！',
    '📝 整体很好，小修即可！',
    '🎉 顺利通过，恭喜！',
    '💪 扎实的研究，值得肯定！'
  ],
  pass: [
    '✅ 达到毕业要求，可以授予学位。',
    '📋 基本合格，需要一些修改。',
    '🔄 建议minor revision后通过。',
    '👌 勉强过关，下次要更认真！'
  ],
  fail: [
    '❌ 未达到要求，需要major revision。',
    '📚 基础薄弱，建议重新学习。',
    '⏸️ 延期答辩，继续完善研究。',
    '💔 很遗憾，但学术是严谨的...'
  ]
}

export default {
  advisorCharacters,
  randomEvents,
  academicMemes,
  easterEggs,
  evaluationTemplates
}
