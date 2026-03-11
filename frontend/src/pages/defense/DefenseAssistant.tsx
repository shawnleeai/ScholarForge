/**
 * 答辩准备助手页面
 */

import React, { useState, useEffect } from 'react'
import {
  Card, Row, Col, Button, Progress, Tabs, List, Checkbox, Tag, Space,
  Typography, Timeline, Badge, Empty, Statistic, Input,
  Collapse, message, Avatar, Descriptions
} from 'antd'
import type { TabsProps } from 'antd'
import {
  CheckSquareOutlined, FilePptOutlined, QuestionCircleOutlined,
  PlayCircleOutlined, TrophyOutlined,
  CheckCircleOutlined, EditOutlined, ReloadOutlined,
  FileTextOutlined, StarOutlined,
  ArrowRightOutlined, TeamOutlined
} from '@ant-design/icons'
import { useParams } from 'react-router-dom'
import { defenseService } from '@/services/defenseService'
import type { DefenseChecklist, DefensePPT, DefenseQA } from '@/types/defense'
import styles from './DefenseAssistant.module.css'
import { EnhancedDefenseSimulation } from '@/components/defense'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Panel } = Collapse

const DefenseAssistantPage: React.FC = () => {
  const { paperId } = useParams<{ paperId: string }>()

  const [activeTab, setActiveTab] = useState('checklist')
  const [checklist, setChecklist] = useState<DefenseChecklist | null>(null)
  const [ppt, setPpt] = useState<DefensePPT | null>(null)
  const [qaList, setQaList] = useState<DefenseQA[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  // 加载数据
  useEffect(() => {
    if (!paperId) return

    let isMounted = true

    const loadData = async () => {
      setLoading(true)
      try {
        // 并行加载数据
        const [checklistRes, qaRes] = await Promise.all([
          defenseService.getChecklist(paperId).catch(err => {
            console.error('获取检查清单失败', err)
            return null
          }),
          defenseService.getQAList({ paperId }).catch(err => {
            console.error('获取问答失败', err)
            return null
          })
        ])

        if (isMounted) {
          if (checklistRes) setChecklist(checklistRes.data)
          if (qaRes) setQaList(qaRes.data)
        }
      } catch (error) {
        console.error('加载数据失败', error)
        if (isMounted) {
          message.error('加载数据失败')
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadData()

    return () => {
      isMounted = false
    }
  }, [paperId])

  // 更新检查项
  const handleCheckItem = async (itemId: string, checked: boolean) => {
    if (!checklist) return

    const newItems = checklist.items.map(item =>
      item.id === itemId ? { ...item, completed: checked } : item
    )

    const newProgress = Math.round(
      (newItems.filter(i => i.completed).length / newItems.length) * 100
    )

    setChecklist({ ...checklist, items: newItems, progress: newProgress })

    try {
      await defenseService.updateChecklist(checklist.id, newItems)
    } catch (error) {
      message.error('保存失败')
    }
  }

  // 生成PPT大纲
  const handleGeneratePPT = async () => {
    if (!paperId) return
    setGenerating(true)
    try {
      const res = await defenseService.generatePPT(paperId)
      setPpt(res.data)
      message.success('PPT大纲生成成功')
    } catch (error) {
      message.error('生成失败')
    } finally {
      setGenerating(false)
    }
  }

  // 生成问答
  const handleGenerateQA = async () => {
    if (!paperId) return
    setLoading(true)
    try {
      const res = await defenseService.generateQA(paperId)
      setQaList(res.data.questions)
      message.success(`生成 ${res.data.generated} 个问题`)
    } catch (error) {
      message.error('生成失败')
    } finally {
      setLoading(false)
    }
  }

  // Tab 内容
  const tabItems: TabsProps['items'] = [
    {
      key: 'checklist',
      label: (
        <span>
          <CheckSquareOutlined /> 准备清单
        </span>
      ),
      children: (
        <div>
          {checklist ? (
            <>
              <Card className={styles.progressCard}>
                <Row gutter={24} align="middle">
                  <Col span={8}>
                    <div className={styles.progressCircle}>
                      <Progress
                        type="circle"
                        percent={checklist.progress}
                        strokeColor={checklist.progress >= 80 ? '#52c41a' : checklist.progress >= 50 ? '#faad14' : '#ff4d4f'}
                        size={120}
                        format={(p) => (
                          <div>
                            <div style={{ fontSize: 28, fontWeight: 'bold' }}>{p}%</div>
                            <div style={{ fontSize: 12 }}>完成度</div>
                          </div>
                        )}
                      />
                    </div>
                  </Col>
                  <Col span={16}>
                    <Descriptions column={2} size="small">
                      <Descriptions.Item label="总任务数">{checklist.items.length} 项</Descriptions.Item>
                      <Descriptions.Item label="已完成">
                        {checklist.items.filter(i => i.completed).length} 项
                      </Descriptions.Item>
                      <Descriptions.Item label="待完成">
                        {checklist.items.filter(i => !i.completed).length} 项
                      </Descriptions.Item>
                      <Descriptions.Item label="预计用时">3-5 天</Descriptions.Item>
                    </Descriptions>
                  </Col>
                </Row>
              </Card>

              <Card title="准备事项" className={styles.checklistCard}>
                <Collapse defaultActiveKey={['文档', 'PPT']}>
                  {['文档', 'PPT', '演练', '准备'].map(category => {
                    const items = checklist.items.filter(i => i.category === category)
                    return (
                      <Panel
                        header={
                          <Space>
                            <Text strong>{category}</Text>
                            <Tag color="blue">
                              {items.filter(i => i.completed).length}/{items.length}
                            </Tag>
                          </Space>
                        }
                        key={category}
                      >
                        <List
                          dataSource={items}
                          renderItem={item => (
                            <List.Item
                              className={item.completed ? styles.completedItem : ''}
                            >
                              <Checkbox
                                checked={item.completed}
                                onChange={(e) => handleCheckItem(item.id, e.target.checked)}
                              >
                                <Text delete={item.completed}>{item.content}</Text>
                              </Checkbox>
                            </List.Item>
                          )}
                        />
                      </Panel>
                    )
                  })}
                </Collapse>
              </Card>
            </>
          ) : (
            <Card className={styles.emptyCard}>
              <Empty
                image={<CheckSquareOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
                description="暂无检查清单"
              />
            </Card>
          )}
        </div>
      )
    },
    {
      key: 'ppt',
      label: (
        <span>
          <FilePptOutlined /> PPT大纲
        </span>
      ),
      children: (
        <div>
          {!ppt ? (
            <Card className={styles.generateCard}>
              <Empty
                image={<FilePptOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />}
                description={
                  <div>
                    <p>基于论文内容自动生成答辩PPT大纲</p>
                    <Button
                      type="primary"
                      icon={<ReloadOutlined />}
                      loading={generating}
                      onClick={handleGeneratePPT}
                    >
                      生成PPT大纲
                    </Button>
                  </div>
                }
              />
            </Card>
          ) : (
            <>
              <Card className={styles.pptHeader}>
                <Row gutter={16} align="middle" justify="space-between">
                  <Col>
                    <Title level={4}>{ppt.outline.title}</Title>
                    <Text type="secondary">模板: {ppt.template}</Text>
                  </Col>
                  <Col>
                    <Space>
                      <Button icon={<ReloadOutlined />} onClick={handleGeneratePPT}>
                        重新生成
                      </Button>
                      <Button type="primary" icon={<DownloadOutlined />}>
                        导出PPT
                      </Button>
                    </Space>
                  </Col>
                </Row>
              </Card>

              <Card className={styles.pptTimeline}>
                <Timeline mode="left">
                  {ppt.outline.slides.map((slide, index) => (
                    <Timeline.Item
                      key={slide.id}
                      dot={
                        slide.type === 'title' ? <TrophyOutlined /> :
                        slide.type === 'thanks' ? <StarOutlined /> :
                        <FileTextOutlined />
                      }
                      label={slide.duration ? `${Math.floor(slide.duration / 60)}:${(slide.duration % 60).toString().padStart(2, '0')}` : ''}
                    >
                      <Card
                        size="small"
                        className={styles.slideCard}
                        title={
                          <Space>
                            <Text strong>{index + 1}. {slide.title}</Text>
                            {slide.type === 'content' && (
                              <Tag color="blue">{slide.duration || 120}s</Tag>
                            )}
                          </Space>
                        }
                        extra={<Button type="link" icon={<EditOutlined />}>编辑</Button>}
                      >
                        <Paragraph style={{ whiteSpace: 'pre-line' }}>
                          {slide.content || '点击编辑内容...'}
                        </Paragraph>
                      </Card>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Card>
            </>
          )}
        </div>
      )
    },
    {
      key: 'qa',
      label: (
        <span>
          <QuestionCircleOutlined /> 问答练习
          <Badge count={qaList.length} style={{ marginLeft: 8 }} />
        </span>
      ),
      children: (
        <div>
          <Card className={styles.qaHeader}>
            <Row gutter={16} align="middle" justify="space-between">
              <Col>
                <Space>
                  <Tag color="green">简单 {qaList.filter(q => q.difficulty === 'easy').length}</Tag>
                  <Tag color="blue">中等 {qaList.filter(q => q.difficulty === 'medium').length}</Tag>
                  <Tag color="red">困难 {qaList.filter(q => q.difficulty === 'hard').length}</Tag>
                </Space>
              </Col>
              <Col>
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  loading={loading}
                  onClick={handleGenerateQA}
                >
                  生成新问题
                </Button>
              </Col>
            </Row>
          </Card>

          <List
            className={styles.qaList}
            grid={{ gutter: 16, column: 1 }}
            dataSource={qaList}
            renderItem={qa => (
              <List.Item>
                <Card
                  className={styles.qaCard}
                  title={
                    <Space>
                      <Tag color={
                        qa.difficulty === 'easy' ? 'green' :
                        qa.difficulty === 'medium' ? 'blue' : 'red'
                      }>
                        {qa.difficulty === 'easy' ? '简单' :
                         qa.difficulty === 'medium' ? '中等' : '困难'}
                      </Tag>
                      <Tag>{qa.category}</Tag>
                    </Space>
                  }
                >
                  <Collapse ghost>
                    <Panel header={<Text strong>{qa.question}</Text>} key="1">
                      <div className={styles.answerBlock}>
                        <Text strong>参考答案：</Text>
                        <Paragraph style={{ marginTop: 8 }}>{qa.answer}</Paragraph>
                      </div>
                    </Panel>
                  </Collapse>
                </Card>
              </List.Item>
            )}
          />
        </div>
      )
    },
    {
      key: 'mock',
      label: (
        <span>
          <PlayCircleOutlined /> 模拟答辩
        </span>
      ),
      children: (
        <div>
          {/* 增强版答辩模拟器 */}
          <EnhancedDefenseSimulation />
        </div>
      )
    }
  ]

  return (
    <div className={styles.container}>
      <Title level={2}>
        <TrophyOutlined /> 答辩准备助手
      </Title>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        type="card"
        size="large"
      />
    </div>
  )
}

// DownloadOutlined component
const DownloadOutlined = () => (
  <svg viewBox="0 0 1024 1024" width="1em" height="1em" fill="currentColor">
    <path d="M505.7 661a8 8 0 0012.6 0l112-141.7c4.1-5.2.4-12.9-6.3-12.9h-74.1V168c0-4.4-3.6-8-8-8h-60c-4.4 0-8 3.6-8 8v338.3H400c-6.7 0-10.4 7.7-6.3 12.9l112 141.8zM878 626h-60c-4.4 0-8 3.6-8 8v154H214V634c0-4.4-3.6-8-8-8h-60c-4.4 0-8 3.6-8 8v198c0 17.7 14.3 32 32 32h684c17.7 0 32-14.3 32-32V634c0-4.4-3.6-8-8-8z" />
  </svg>
)

export default DefenseAssistantPage
