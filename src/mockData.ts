import type { TreeNode } from './types'

export const mockNodes: Record<string, TreeNode> = {
  root: {
    id: 'root',
    content: 'AI 正在深刻改变教育的形态',
    parentId: null,
    messages: [
      { role: 'user', text: 'AI 对教育有哪些深远影响？' },
      {
        role: 'assistant',
        text: 'AI 正在从多个维度重塑教育：它使个性化学习成为可能，让每个学生都能按自己的节奏和方式学习；同时也催生了智能辅导系统，改变了教师的角色定位。这场变革不仅影响教学方法，更在重新定义"学习"本身的意义。',
      },
    ],
  },
  node_personal: {
    id: 'node_personal',
    content: '个性化学习路径让每个学生按自己节奏前进',
    parentId: 'root',
    messages: [
      { role: 'user', text: '个性化学习路径具体是怎么实现的？' },
      {
        role: 'assistant',
        text: 'AI 通过持续追踪学生的答题行为、响应时间和错误模式，建立个人学习画像。系统据此动态调整题目难度和知识点顺序，确保学生始终处于"略有挑战但不至于挫败"的最佳学习区间。每个学生走的路径都不同，但目标一致。',
      },
    ],
  },
  node_adaptive: {
    id: 'node_adaptive',
    content: '自适应题库根据错误模式动态调整难度',
    parentId: 'node_personal',
    messages: [
      { role: 'user', text: '自适应题库背后的算法原理是什么？' },
      {
        role: 'assistant',
        text: '主流方案基于项目反应理论（IRT）或知识图谱。IRT 通过统计模型估算学生能力值，每道题都有难度、区分度参数，系统选择最能区分当前能力水平的题目。知识图谱方案则追踪概念掌握状态，优先补强薄弱的前置知识节点。两者都依赖大量历史数据训练。',
      },
    ],
  },
  node_pace: {
    id: 'node_pace',
    content: '学习节奏调控避免了统一进度带来的两极分化',
    parentId: 'node_personal',
    messages: [
      { role: 'user', text: '统一进度的问题在哪里，AI 如何解决？' },
      {
        role: 'assistant',
        text: '传统班级教学用同一速度推进，聪明的学生觉得无聊、基础弱的学生跟不上，久而久之两极分化。AI 允许每人"异步学习"——快者可超前探索拓展内容，慢者得到额外巩固练习，系统自动维护进度差异，教师也能通过仪表板看到全班状态并适时介入。',
      },
    ],
  },
  node_tutor: {
    id: 'node_tutor',
    content: '智能辅导系统提供全天候一对一答疑支持',
    parentId: 'root',
    messages: [
      { role: 'user', text: '智能辅导系统和普通搜索有什么本质区别？' },
      {
        role: 'assistant',
        text: '搜索返回信息，辅导系统引导思考。优秀的 AI 辅导不直接给答案，而是通过追问帮学生自己推导出结论——这正是苏格拉底式教学法。此外辅导系统有上下文记忆，知道这个学生卡在哪里、之前犯过什么错，回应更有针对性，而不是通用答案。',
      },
    ],
  },
  node_socratic: {
    id: 'node_socratic',
    content: '苏格拉底式对话机器人引导学生自主推导结论',
    parentId: 'node_tutor',
    messages: [
      { role: 'user', text: '苏格拉底式 AI 辅导的实际效果如何？' },
      {
        role: 'assistant',
        text: '研究表明，这种方式比直接告知答案的记忆留存率高出 40% 以上。学生在被追问"为什么""如果换一种情况呢"的过程中，被迫激活和重组已有知识，形成更深层的理解。麻省理工、可汗学院的实验都验证了这一点，但实现难点在于让 AI 判断何时追问、何时直接解释。',
      },
    ],
  },
  node_teacher: {
    id: 'node_teacher',
    content: '教师角色从知识传递者转向学习设计者',
    parentId: 'root',
    messages: [
      { role: 'user', text: 'AI 会取代教师吗？' },
      {
        role: 'assistant',
        text: '不会取代，但会深刻重塑。AI 接管了重复性的讲解、批改、答疑工作后，教师得以聚焦在 AI 不擅长的事：激发好奇心、引导价值观讨论、识别学生情绪状态、设计有创造性的学习体验。教师的核心价值从"传递知识"转向"设计让知识真正发生的场域"。',
      },
    ],
  },
  node_design: {
    id: 'node_design',
    content: '教师成为课程设计者，专注激发好奇心与创造力',
    parentId: 'node_teacher',
    messages: [
      { role: 'user', text: '未来教师需要什么新技能？' },
      {
        role: 'assistant',
        text: '最关键的是"学习设计"能力：理解认知科学原理、设计促进深度思考的任务序列、会读懂 AI 生成的学生数据并作出教学决策。其次是情感连接能力，在 AI 处理知识传递的背景下，人与人之间真实的关怀和信任感变得更稀缺也更珍贵。编程和 AI 工具使用则是基础门槛。',
      },
    ],
  },
}

export const rootId = 'root'
