import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { OrganizationService } from '@core/services/organization.service';
import { TranslationService } from '@core/services/translation.service';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog/confirm-dialog.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';
import { OrgMemberDisplay } from './member-management.types';

@Component({
  selector: 'app-member-management',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    LoadingSpinnerComponent,
    UserAvatarComponent,
    ConfirmDialogComponent,
    TranslatePipe,
  ],
  templateUrl: './member-management.component.html',
  styleUrls: ['./member-management.component.scss'],
})
export class MemberManagementComponent implements OnInit {
  private orgService = inject(OrganizationService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  members = signal<OrgMemberDisplay[]>([]);
  confirmRemove = signal<OrgMemberDisplay | null>(null);

  showInvite = false;
  inviteEmail = '';
  inviteRole = 'member';

  private orgId = '';

  ngOnInit(): void {
    this.orgService.list().subscribe({
      next: (res) => {
        if (res.results[0]) {
          this.orgId = res.results[0].id;
          this.loadMembers();
        } else {
          this.loading.set(false);
        }
      },
    });
  }

  private loadMembers(): void {
    this.orgService.getMembers(this.orgId).subscribe({
      next: (res) => {
        this.members.set(res as any);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  invite(): void {
    this.orgService
      .addMember(this.orgId, { email: this.inviteEmail, role: this.inviteRole })
      .subscribe({
        next: () => {
          this.toast.success(this.i18n.t('members.invited'));
          this.inviteEmail = '';
          this.showInvite = false;
          this.loadMembers();
        },
        error: () => this.toast.error(this.i18n.t('members.inviteFailed')),
      });
  }

  changeRole(member: OrgMemberDisplay, role: string): void {
    this.orgService.updateMember(this.orgId, member.id, { role }).subscribe({
      next: () => {
        this.members.update((ms) =>
          ms.map((m) => (m.id === member.id ? { ...m, role } : m))
        );
        this.toast.success(this.i18n.t('members.roleUpdated'));
      },
      error: () => this.toast.error(this.i18n.t('members.roleUpdateFailed')),
    });
  }

  removeMember(member: OrgMemberDisplay): void {
    this.confirmRemove.set(member);
  }

  doRemove(): void {
    const member = this.confirmRemove();
    if (!member) return;
    this.orgService.removeMember(this.orgId, member.id).subscribe({
      next: () => {
        this.members.update((ms) => ms.filter((m) => m.id !== member.id));
        this.confirmRemove.set(null);
        this.toast.success(this.i18n.t('members.removed'));
      },
      error: () => this.toast.error(this.i18n.t('members.removeFailed')),
    });
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString(this.i18n.getLocale(), {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }
}
