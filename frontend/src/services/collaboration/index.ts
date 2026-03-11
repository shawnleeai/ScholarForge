/**
 * Yjs Collaboration Services
 * 导出所有Yjs协作相关模块
 */

export {
  YjsDocumentManager,
  YjsDocumentManagerFactory,
  type UserInfo,
  type DocumentMetadata,
  type CollaborationState,
  type YjsUpdateCallback,
  type AwarenessChangeCallback,
  type StatusChangeCallback,
  type SyncChangeCallback,
} from './YjsDocumentManager'

export {
  useYjsCollaboration,
  useYjsTiptap,
  useAwarenessCursors,
  type UseYjsCollaborationOptions,
  type UseYjsCollaborationReturn,
  type UseYjsTiptapOptions,
} from './useYjsCollaboration'

export {
  VersionManager,
  formatVersionTime,
  formatRelativeTime,
  type VersionInfo,
  type VersionDiff,
  type VersionCompareResult,
} from './VersionManager'

export {
  CommentManager,
  CommentManagerFactory,
  type Comment,
  type CommentAuthor,
  type CommentPosition,
  type CommentStatus,
  type CommentReply,
  type CreateCommentInput,
  type AddReplyInput,
} from './CommentManager'
