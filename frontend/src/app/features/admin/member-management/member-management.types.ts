/**
 * Member Management component types and i18n keys
 */
export interface OrgMemberDisplay {
  id: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    avatar: string | null;
  };
  role: string;
  joined_at: string;
}

export interface MemberManagementI18nKeys {
  title: string;
  invite: string;
  inviteMember: string;
  role: string;
  roleMember: string;
  roleAdmin: string;
  roleOwner: string;
  send: string;
  memberCol: string;
  joined: string;
  actions: string;
  removeTitle: string;
  removeMessage: string;
  invited: string;
  inviteFailed: string;
  roleUpdated: string;
  roleUpdateFailed: string;
  removed: string;
  removeFailed: string;
}

export const MEMBER_MANAGEMENT_I18N_KEYS: MemberManagementI18nKeys = {
  title: 'members.title',
  invite: 'members.invite',
  inviteMember: 'members.inviteMember',
  role: 'members.role',
  roleMember: 'members.roleMember',
  roleAdmin: 'members.roleAdmin',
  roleOwner: 'members.roleOwner',
  send: 'members.send',
  memberCol: 'members.memberCol',
  joined: 'members.joined',
  actions: 'members.actions',
  removeTitle: 'members.removeTitle',
  removeMessage: 'members.removeMessage',
  invited: 'members.invited',
  inviteFailed: 'members.inviteFailed',
  roleUpdated: 'members.roleUpdated',
  roleUpdateFailed: 'members.roleUpdateFailed',
  removed: 'members.removed',
  removeFailed: 'members.removeFailed',
};
