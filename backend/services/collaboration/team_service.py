"""
研究团队服务
处理团队创建、成员管理、项目协作等核心业务逻辑
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from team_models import (
    ResearchTeam, TeamMember, TeamRole, JoinStatus, TeamActivity,
    TeamInvitation, JoinApplication, ResearchProject, TeamResource,
    CreateTeamRequest, UpdateTeamRequest, InviteMemberRequest,
    CreateProjectRequest, ROLE_PERMISSIONS, TeamPermission
)


class TeamService:
    """研究团队服务"""

    def __init__(self):
        # 内存存储 (实际项目中使用数据库)
        self._teams: Dict[str, ResearchTeam] = {}
        self._invitations: Dict[str, TeamInvitation] = {}
        self._applications: Dict[str, JoinApplication] = {}
        self._activities: List[TeamActivity] = []

        # 初始化示例数据
        self._init_sample_data()

    def _init_sample_data(self):
        """初始化示例数据"""
        # 示例团队
        sample_team = ResearchTeam(
            id=str(uuid.uuid4()),
            name="机器学习研究组",
            description="专注于深度学习和自然语言处理的研究团队",
            institution="某某大学",
            research_fields=["机器学习", "自然语言处理", "计算机视觉"],
            created_by="user_001",
            created_at=datetime.now(),
            is_public=True,
            join_type="application",
            members=[
                TeamMember(
                    user_id="user_001",
                    username="张教授",
                    email="zhang@example.edu",
                    role=TeamRole.OWNER,
                    join_status=JoinStatus.APPROVED,
                    contributions=45,
                    research_interests=["深度学习", "NLP"]
                ),
                TeamMember(
                    user_id="user_002",
                    username="李博士",
                    email="li@example.edu",
                    role=TeamRole.ADMIN,
                    join_status=JoinStatus.APPROVED,
                    contributions=28,
                    research_interests=["计算机视觉", "强化学习"]
                ),
                TeamMember(
                    user_id="user_003",
                    username="王同学",
                    email="wang@example.edu",
                    role=TeamRole.MEMBER,
                    join_status=JoinStatus.APPROVED,
                    contributions=12,
                    research_interests=["机器学习", "数据挖掘"]
                ),
            ],
            projects=[
                ResearchProject(
                    id=str(uuid.uuid4()),
                    name="大语言模型微调研究",
                    description="研究LLM在特定领域的微调方法",
                    status="active",
                    start_date=datetime.now() - timedelta(days=180),
                    leader_id="user_001",
                    members=["user_001", "user_002", "user_003"],
                    progress=65
                ),
                ResearchProject(
                    id=str(uuid.uuid4()),
                    name="多模态学习框架",
                    description="构建统一的多模态学习架构",
                    status="active",
                    start_date=datetime.now() - timedelta(days=90),
                    leader_id="user_002",
                    members=["user_002", "user_003"],
                    progress=40
                ),
            ],
            stats={
                "total_publications": 12,
                "active_projects": 2,
                "completed_projects": 5,
                "total_contributions": 156
            }
        )
        self._teams[sample_team.id] = sample_team

    # ============ 团队管理 ============

    async def create_team(
        self,
        user_id: str,
        username: str,
        email: str,
        request: CreateTeamRequest
    ) -> ResearchTeam:
        """创建研究团队"""
        team_id = str(uuid.uuid4())

        team = ResearchTeam(
            id=team_id,
            name=request.name,
            description=request.description,
            institution=request.institution,
            research_fields=request.research_fields,
            created_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_public=request.is_public,
            join_type=request.join_type,
            members=[
                TeamMember(
                    user_id=user_id,
                    username=username,
                    email=email,
                    role=TeamRole.OWNER,
                    join_status=JoinStatus.APPROVED,
                    join_date=datetime.now()
                )
            ],
            stats={
                "total_publications": 0,
                "active_projects": 0,
                "completed_projects": 0,
                "total_contributions": 0
            }
        )

        self._teams[team_id] = team

        # 记录活动
        await self._add_activity(team_id, user_id, username, "create_team", details={"team_name": request.name})

        return team

    async def get_team(self, team_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取团队详情"""
        team = self._teams.get(team_id)
        if not team:
            return None

        # 计算权限
        is_member = False
        is_owner = False
        can_manage = False

        if user_id:
            member = next((m for m in team.members if m.user_id == user_id), None)
            if member:
                is_member = True
                is_owner = member.role == TeamRole.OWNER
                can_manage = self._has_permission(member.role, TeamPermission.MANAGE_MEMBERS)

        return {
            "team": team,
            "is_member": is_member,
            "is_owner": is_owner,
            "member_count": len(team.members),
            "can_manage": can_manage
        }

    async def update_team(
        self,
        team_id: str,
        user_id: str,
        request: UpdateTeamRequest
    ) -> Optional[ResearchTeam]:
        """更新团队信息"""
        team = self._teams.get(team_id)
        if not team:
            return None

        # 检查权限
        if not await self._check_permission(team_id, user_id, TeamPermission.MANAGE_MEMBERS):
            raise PermissionError("没有权限更新团队信息")

        # 更新字段
        if request.name is not None:
            team.name = request.name
        if request.description is not None:
            team.description = request.description
        if request.institution is not None:
            team.institution = request.institution
        if request.research_fields is not None:
            team.research_fields = request.research_fields
        if request.avatar_url is not None:
            team.avatar_url = request.avatar_url
        if request.is_public is not None:
            team.is_public = request.is_public
        if request.join_type is not None:
            team.join_type = request.join_type
        if request.max_members is not None:
            team.max_members = request.max_members

        team.updated_at = datetime.now()

        # 记录活动
        member = next((m for m in team.members if m.user_id == user_id), None)
        await self._add_activity(team_id, user_id, member.username if member else "Unknown", "update_team")

        return team

    async def delete_team(self, team_id: str, user_id: str) -> bool:
        """删除团队"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 只有所有者可以删除
        if team.created_by != user_id:
            raise PermissionError("只有团队所有者可以删除团队")

        del self._teams[team_id]
        return True

    # ============ 成员管理 ============

    async def invite_member(
        self,
        team_id: str,
        inviter_id: str,
        request: InviteMemberRequest
    ) -> TeamInvitation:
        """邀请成员加入团队"""
        team = self._teams.get(team_id)
        if not team:
            raise ValueError("团队不存在")

        # 检查权限
        if not await self._check_permission(team_id, inviter_id, TeamPermission.INVITE_MEMBERS):
            raise PermissionError("没有权限邀请成员")

        # 检查成员数量
        if len(team.members) >= team.max_members:
            raise ValueError("团队人数已达上限")

        # 创建邀请
        invitation = TeamInvitation(
            id=str(uuid.uuid4()),
            team_id=team_id,
            inviter_id=inviter_id,
            invitee_email=request.email,
            role=request.role,
            message=request.message,
            expires_at=datetime.now() + timedelta(days=7)
        )

        self._invitations[invitation.id] = invitation

        # 记录活动
        inviter = next((m for m in team.members if m.user_id == inviter_id), None)
        await self._add_activity(
            team_id, inviter_id, inviter.username if inviter else "Unknown",
            "invite_member", details={"email": request.email}
        )

        return invitation

    async def accept_invitation(self, invitation_id: str, user_id: str, username: str, email: str) -> bool:
        """接受邀请"""
        invitation = self._invitations.get(invitation_id)
        if not invitation or invitation.status != "pending":
            return False

        if invitation.expires_at < datetime.now():
            invitation.status = "expired"
            return False

        team = self._teams.get(invitation.team_id)
        if not team:
            return False

        # 添加成员
        member = TeamMember(
            user_id=user_id,
            username=username,
            email=email,
            role=invitation.role,
            join_status=JoinStatus.APPROVED,
            join_date=datetime.now()
        )
        team.members.append(member)

        invitation.status = "accepted"

        # 记录活动
        await self._add_activity(team.id, user_id, username, "join_team", details={"via": "invitation"})

        return True

    async def apply_to_join(
        self,
        team_id: str,
        applicant_id: str,
        applicant_name: str,
        message: Optional[str] = None,
        research_interests: List[str] = []
    ) -> JoinApplication:
        """申请加入团队"""
        team = self._teams.get(team_id)
        if not team:
            raise ValueError("团队不存在")

        if team.join_type == "invite":
            raise ValueError("该团队仅支持邀请加入")

        application = JoinApplication(
            id=str(uuid.uuid4()),
            team_id=team_id,
            applicant_id=applicant_id,
            applicant_name=applicant_name,
            message=message,
            research_interests=research_interests
        )

        self._applications[application.id] = application

        return application

    async def process_application(
        self,
        team_id: str,
        application_id: str,
        processor_id: str,
        approve: bool
    ) -> bool:
        """处理加入申请"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 检查权限
        if not await self._check_permission(team_id, processor_id, TeamPermission.MANAGE_MEMBERS):
            raise PermissionError("没有权限处理申请")

        application = self._applications.get(application_id)
        if not application or application.team_id != team_id:
            return False

        application.status = "approved" if approve else "rejected"

        if approve:
            # 添加成员
            member = TeamMember(
                user_id=application.applicant_id,
                username=application.applicant_name,
                email="",  # 从用户系统获取
                role=TeamRole.MEMBER,
                join_status=JoinStatus.APPROVED,
                join_date=datetime.now()
            )
            team.members.append(member)

            # 记录活动
            processor = next((m for m in team.members if m.user_id == processor_id), None)
            await self._add_activity(
                team_id, application.applicant_id, application.applicant_name,
                "join_team", details={"via": "application", "approved_by": processor.username if processor else None}
            )

        return True

    async def remove_member(self, team_id: str, owner_id: str, member_id: str) -> bool:
        """移除成员"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 检查权限
        if not await self._check_permission(team_id, owner_id, TeamPermission.MANAGE_MEMBERS):
            raise PermissionError("没有权限移除成员")

        # 不能移除自己
        if member_id == owner_id:
            raise ValueError("不能移除自己")

        # 不能移除所有者
        member = next((m for m in team.members if m.user_id == member_id), None)
        if member and member.role == TeamRole.OWNER:
            raise ValueError("不能移除团队所有者")

        team.members = [m for m in team.members if m.user_id != member_id]

        # 记录活动
        remover = next((m for m in team.members if m.user_id == owner_id), None)
        await self._add_activity(
            team_id, owner_id, remover.username if remover else "Unknown",
            "remove_member", details={"removed_id": member_id}
        )

        return True

    async def update_member_role(
        self,
        team_id: str,
        owner_id: str,
        member_id: str,
        new_role: TeamRole
    ) -> bool:
        """更新成员角色"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 检查权限
        if not await self._check_permission(team_id, owner_id, TeamPermission.MANAGE_MEMBERS):
            raise PermissionError("没有权限修改成员角色")

        # 不能修改所有者
        if member_id == team.created_by:
            raise ValueError("不能修改团队所有者的角色")

        member = next((m for m in team.members if m.user_id == member_id), None)
        if not member:
            return False

        member.role = new_role

        # 记录活动
        updater = next((m for m in team.members if m.user_id == owner_id), None)
        await self._add_activity(
            team_id, owner_id, updater.username if updater else "Unknown",
            "update_role", details={"member_id": member_id, "new_role": new_role.value}
        )

        return True

    async def leave_team(self, team_id: str, user_id: str) -> bool:
        """离开团队"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 所有者不能离开，需要先转让所有权
        member = next((m for m in team.members if m.user_id == user_id), None)
        if member and member.role == TeamRole.OWNER:
            raise ValueError("团队所有者不能离开，请先转让所有权")

        team.members = [m for m in team.members if m.user_id != user_id]

        # 记录活动
        await self._add_activity(team_id, user_id, member.username if member else "Unknown", "leave_team")

        return True

    # ============ 项目管理 ============

    async def create_project(
        self,
        team_id: str,
        user_id: str,
        request: CreateProjectRequest
    ) -> ResearchProject:
        """创建研究项目"""
        team = self._teams.get(team_id)
        if not team:
            raise ValueError("团队不存在")

        # 检查权限
        if not await self._check_permission(team_id, user_id, TeamPermission.MANAGE_PROJECTS):
            raise PermissionError("没有权限创建项目")

        project = ResearchProject(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            start_date=request.start_date,
            end_date=request.end_date,
            leader_id=request.leader_id or user_id,
            members=[user_id]
        )

        team.projects.append(project)
        team.stats["active_projects"] = len([p for p in team.projects if p.status == "active"])

        # 记录活动
        creator = next((m for m in team.members if m.user_id == user_id), None)
        await self._add_activity(
            team_id, user_id, creator.username if creator else "Unknown",
            "create_project", details={"project_name": request.name}
        )

        return project

    # ============ 搜索和列表 ============

    async def search_teams(
        self,
        query: Optional[str] = None,
        institution: Optional[str] = None,
        research_field: Optional[str] = None,
        is_public: Optional[bool] = True,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """搜索团队"""
        results = list(self._teams.values())

        # 只显示公开团队
        if is_public:
            results = [t for t in results if t.is_public]

        # 关键词搜索
        if query:
            query_lower = query.lower()
            results = [
                t for t in results
                if query_lower in t.name.lower()
                or (t.description and query_lower in t.description.lower())
                or any(query_lower in f.lower() for f in t.research_fields)
            ]

        # 机构筛选
        if institution:
            results = [t for t in results if t.institution and institution.lower() in t.institution.lower()]

        # 研究领域筛选
        if research_field:
            results = [t for t in results if research_field in t.research_fields]

        # 分页
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        results = results[start:end]

        return {
            "teams": results,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def get_user_teams(self, user_id: str) -> List[ResearchTeam]:
        """获取用户加入的所有团队"""
        return [
            team for team in self._teams.values()
            if any(m.user_id == user_id for m in team.members)
        ]

    async def get_team_activities(self, team_id: str, limit: int = 50) -> List[TeamActivity]:
        """获取团队活动"""
        activities = [a for a in self._activities if a.team_id == team_id]
        return sorted(activities, key=lambda x: x.created_at, reverse=True)[:limit]

    # ============ 辅助方法 ============

    def _has_permission(self, role: TeamRole, permission: TeamPermission) -> bool:
        """检查角色是否有权限"""
        return permission in ROLE_PERMISSIONS.get(role, [])

    async def _check_permission(self, team_id: str, user_id: str, permission: TeamPermission) -> bool:
        """检查用户是否有权限"""
        team = self._teams.get(team_id)
        if not team:
            return False

        # 团队所有者拥有所有权限
        if team.created_by == user_id:
            return True

        member = next((m for m in team.members if m.user_id == user_id), None)
        if not member:
            return False

        return self._has_permission(member.role, permission)

    async def _add_activity(
        self,
        team_id: str,
        user_id: str,
        username: str,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """添加团队活动"""
        activity = TeamActivity(
            id=str(uuid.uuid4()),
            team_id=team_id,
            user_id=user_id,
            username=username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            details=details
        )
        self._activities.append(activity)


# 服务实例
team_service = TeamService()
