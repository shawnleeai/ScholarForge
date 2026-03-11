/**
 * Voice Writing Panel
 * 语音写作面板 - 支持语音输入、口语转学术化、语音播报
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Tag,
  Alert,
  Tooltip,
  Select,
  Badge,
  Divider,
  message,
  Spin
} from 'antd';
import {
  AudioOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  SoundOutlined,
  EditOutlined,
  CheckOutlined,
  DeleteOutlined,
  LoadingOutlined,
  MessageOutlined,
  FileTextOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  TeamOutlined,
  BulbOutlined
} from '@ant-design/icons';
import { voiceWritingService } from '../../services/aiVoiceService';
import styles from './VoiceWriting.module.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface VoiceWritingPanelProps {
  currentText?: string;
  onTextInsert?: (text: string, position?: string) => void;
  onTextReplace?: (text: string, range?: { start: number; end: number }) => void;
  paperContext?: string;
}

type SectionType = 'general' | 'abstract' | 'introduction' | 'method' | 'results' | 'discussion' | 'conclusion';

interface TranscriptionResult {
  transcribed_text: string;
  academic_text: string;
  section_type: string;
  success: boolean;
}

export const VoiceWritingPanel: React.FC<VoiceWritingPanelProps> = ({
  currentText = '',
  onTextInsert,
  onTextReplace,
  paperContext = ''
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sectionType, setSectionType] = useState<SectionType>('general');
  const [transcribedText, setTranscribedText] = useState('');
  const [academicText, setAcademicText] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [showComparison, setShowComparison] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  // 开始录音
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // 创建音频分析器用于可视化
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      // 开始音量监测
      monitorAudioLevel();

      // 创建MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.start(100); // 每100ms收集一次数据
      setIsRecording(true);
      setRecordingTime(0);

      // 开始计时
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      message.success('开始录音，请说话...');
    } catch (error) {
      message.error('无法访问麦克风，请检查权限设置');
      console.error('录音错误:', error);
    }
  }, []);

  // 监测音量级别
  const monitorAudioLevel = () => {
    if (!analyserRef.current || !isRecording) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    setAudioLevel(average);

    requestAnimationFrame(monitorAudioLevel);
  };

  // 停止录音并处理
  const stopRecording = useCallback(async () => {
    if (!mediaRecorderRef.current) return;

    setIsRecording(false);
    setIsProcessing(true);

    // 停止计时
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }

    // 停止音频上下文
    if (audioContextRef.current) {
      await audioContextRef.current.close();
    }

    mediaRecorderRef.current.stop();
    mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());

    mediaRecorderRef.current.onstop = async () => {
      try {
        // 合并音频块
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });

        // 发送到服务端处理
        const result = await voiceWritingService.transcribeAndProcess(
          audioBlob,
          paperContext,
          sectionType
        );

        if (result.success) {
          setTranscribedText(result.transcribed_text);
          setAcademicText(result.academic_text);
          setShowComparison(true);
          message.success('语音处理完成！');
        } else {
          message.error(result.error || '处理失败');
        }
      } catch (error) {
        message.error('语音处理出错');
        console.error(error);
      } finally {
        setIsProcessing(false);
      }
    };
  }, [sectionType, paperContext]);

  // 插入到编辑器
  const handleInsert = () => {
    if (academicText && onTextInsert) {
      onTextInsert(academicText);
      message.success('已插入到文档');
      clearResults();
    }
  };

  // 替换选中文本
  const handleReplace = () => {
    if (academicText && onTextReplace) {
      onTextReplace(academicText);
      message.success('已替换文本');
      clearResults();
    }
  };

  // 清空结果
  const clearResults = () => {
    setTranscribedText('');
    setAcademicText('');
    setShowComparison(false);
  };

  // 朗读学术文本
  const handleReadAloud = async () => {
    if (!academicText) return;

    try {
      const audioBlob = await voiceWritingService.textToSpeech(academicText);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      message.error('语音播放失败');
    }
  };

  // 格式化时间
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 章节类型配置
  const sectionTypes: { value: SectionType; label: string; icon: React.ReactNode; color: string }[] = [
    { value: 'general', label: '通用写作', icon: <EditOutlined />, color: '#1890ff' },
    { value: 'abstract', label: '摘要', icon: <FileTextOutlined />, color: '#52c41a' },
    { value: 'introduction', label: '引言', icon: <BulbOutlined />, color: '#722ed1' },
    { value: 'method', label: '方法', icon: <ExperimentOutlined />, color: '#fa8c16' },
    { value: 'results', label: '结果', icon: <BarChartOutlined />, color: '#13c2c2' },
    { value: 'discussion', label: '讨论', icon: <TeamOutlined />, color: '#eb2f96' },
    { value: 'conclusion', label: '结论', icon: <CheckOutlined />, color: '#1890ff' }
  ];

  return (
    <Card className={styles.voiceWritingPanel} bordered={false}>
      <div className={styles.header}>
        <Title level={5} className={styles.title}>
          <AudioOutlined /> 语音写作助手
          <Badge count="Beta" style={{ backgroundColor: '#722ed1', marginLeft: 8 }} />
        </Title>
        <Text type="secondary" className={styles.subtitle}>
          按住说话，AI自动转为学术表达
        </Text>
      </div>

      <Alert
        message="使用提示"
        description="选择当前章节类型，按住麦克风按钮说话，系统会自动将口语转换为学术化表达。支持中文和英文混合输入。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* 章节类型选择 */}
      <div className={styles.sectionSelector}>
        <Text strong style={{ marginRight: 12 }}>当前章节：</Text>
        <Select
          value={sectionType}
          onChange={setSectionType}
          style={{ width: 150 }}
          disabled={isRecording}
        >
          {sectionTypes.map(type => (
            <Option key={type.value} value={type.value}>
              <Space>
                <span style={{ color: type.color }}>{type.icon}</span>
                {type.label}
              </Space>
            </Option>
          ))}
        </Select>
      </div>

      {/* 录音控制区 */}
      <div className={styles.recordingArea}>
        <div className={styles.recordingButtonWrapper}>
          <Button
            type="primary"
            shape="circle"
            size="large"
            className={`${styles.recordButton} ${isRecording ? styles.recording : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <LoadingOutlined spin />
            ) : isRecording ? (
              <PauseCircleOutlined />
            ) : (
              <AudioOutlined />
            )}
          </Button>

          {isRecording && (
            <div className={styles.recordingIndicator}>
              <Badge status="processing" text="录音中" />
              <Text className={styles.timer}>{formatTime(recordingTime)}</Text>
            </div>
          )}
        </div>

        {/* 音频可视化 */}
        {isRecording && (
          <div className={styles.audioVisualizer}>
            {[...Array(20)].map((_, i) => (
              <div
                key={i}
                className={styles.bar}
                style={{
                  height: `${Math.max(10, Math.min(100, audioLevel * Math.random() * 2))}%`,
                  animationDelay: `${i * 0.05}s`
                }}
              />
            ))}
          </div>
        )}
      </div>

      {/* 处理中状态 */}
      {isProcessing && (
        <div className={styles.processingIndicator}>
          <Spin size="large" tip="正在处理语音，转换为学术文本..." />
        </div>
      )}

      {/* 结果对比区 */}
      {showComparison && (
        <div className={styles.resultArea}>
          <Divider>转换结果</Divider>

          <div className={styles.comparisonCards}>
            {/* 原始转写 */}
            <Card
              size="small"
              title={
                <Space>
                  <MessageOutlined />
                  <Text strong>原始语音</Text>
                  <Tag color="default">口语</Tag>
                </Space>
              }
              className={styles.originalCard}
            >
              <Paragraph>{transcribedText || '无内容'}</Paragraph>
            </Card>

            {/* 转换箭头 */}
            <div className={styles.arrowContainer}>
              <div className={styles.arrow}>→</div>
              <Text type="secondary" className={styles.arrowText}>
                AI学术化
              </Text>
            </div>

            {/* 学术文本 */}
            <Card
              size="small"
              title={
                <Space>
                  <FileTextOutlined />
                  <Text strong>学术表达</Text>
                  <Tag color="blue">正式</Tag>
                </Space>
              }
              className={styles.academicCard}
              extra={
                <Tooltip title="朗读">
                  <Button
                    type="text"
                    size="small"
                    icon={<SoundOutlined />}
                    onClick={handleReadAloud}
                  />
                </Tooltip>
              }
            >
              <Paragraph className={styles.academicText}>
                {academicText || '无内容'}
              </Paragraph>
            </Card>
          </div>

          {/* 操作按钮 */}
          <div className={styles.actionButtons}>
            <Space>
              <Button type="primary" icon={<CheckOutlined />} onClick={handleInsert}>
                插入文档
              </Button>
              {onTextReplace && (
                <Button icon={<EditOutlined />} onClick={handleReplace}>
                  替换选中文本
                </Button>
              )}
              <Button icon={<DeleteOutlined />} onClick={clearResults}>
                清空
              </Button>
            </Space>
          </div>
        </div>
      )}

      {/* 快捷指令提示 */}
      <div className={styles.voiceCommands}>
        <Text type="secondary" strong>支持的语音指令：</Text>
        <Space wrap style={{ marginTop: 8 }}>
          <Tag>"在引言部分插入..."</Tag>
          <Tag>"润色这段文字"</Tag>
          <Tag>"继续写下去"</Tag>
          <Tag>"生成摘要"</Tag>
          <Tag>"添加参考文献"</Tag>
        </Space>
      </div>
    </Card>
  );
};

export default VoiceWritingPanel;
