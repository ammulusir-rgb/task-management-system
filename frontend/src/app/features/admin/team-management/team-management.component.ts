import {
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TeamService, Team, TeamMember } from '@core/services/team.service';
import { OrganizationService } from '@core/services/organization.service';
import { UserManagementService } from '@core/services/user-management.service';
import { TranslationService } from '@core/services/translation.service';
import { Organization, User } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog/confirm-dialog.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-team-management',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    LoadingSpinnerComponent,
    UserAvatarComponent,
    ConfirmDialogComponent,
    TranslatePipe,
  ],
  templateUrl: './team-management.component.html',
  styleUrls: ['./team-management.component.scss'],
})
export class TeamManagementComponent implements OnInit {
  private teamService = inject(TeamService);
  private orgService = inject(OrganizationService);
  private userService = inject(UserManagementService);
  private toast = inject(ToastService);
  i18n = inject(TranslationService);

  loading = signal(true);
  teams = signal<Team[]>([]);
  orgs = signal<Organization[]>([]);
  selectedOrgId = '';

  // Create form
  showCreate = false;
  newTeam = { name: '', description: '' };

  // Team detail
  selectedTeam = signal<Team | null>(null);
  teamMembers = signal<TeamMember[]>([]);
  availableUsers = signal<User[]>([]);
  addUserId = '';

  // Confirm delete
  confirmDeleteTeam = signal<Team | null>(null);

  ngOnInit(): void {
    this.orgService.list().subscribe({
      next: (res) => {
        this.orgs.set(res.results);
        if (res.results.length > 0) {
          this.selectedOrgId = res.results[0].id;
          this.loadTeams();
        } else {
          this.loading.set(false);
        }
      },
      error: () => this.loading.set(false),
    });
  }

  loadTeams(): void {
    this.loading.set(true);
    this.teamService.list({ organization: this.selectedOrgId }).subscribe({
      next: (res) => {
        this.teams.set(res.results);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  onOrgChange(): void {
    this.selectedTeam.set(null);
    this.loadTeams();
  }

  createTeam(): void {
    this.teamService
      .create({
        organization: this.selectedOrgId,
        name: this.newTeam.name,
        description: this.newTeam.description,
      })
      .subscribe({
        next: () => {
          this.toast.success(this.i18n.t('teamMgmt.created'));
          this.showCreate = false;
          this.newTeam = { name: '', description: '' };
          this.loadTeams();
        },
        error: () => this.toast.error(this.i18n.t('teamMgmt.createFailed')),
      });
  }

  selectTeam(team: Team): void {
    this.selectedTeam.set(team);
    this.loadTeamMembers(team.id);
    this.loadAvailableUsers();
  }

  private loadTeamMembers(teamId: string): void {
    this.teamService.getMembers(teamId).subscribe({
      next: (members) => this.teamMembers.set(members),
    });
  }

  private loadAvailableUsers(): void {
    this.userService.list({ page_size: 100 }).subscribe({
      next: (res) => this.availableUsers.set(res.results),
    });
  }

  addMember(): void {
    const team = this.selectedTeam();
    if (!team || !this.addUserId) return;
    this.teamService
      .addMember(team.id, { user_id: this.addUserId })
      .subscribe({
        next: () => {
          this.toast.success(this.i18n.t('teamMgmt.memberAdded'));
          this.addUserId = '';
          this.loadTeamMembers(team.id);
        },
        error: (err) => {
          const msg = err?.error?.error?.message || this.i18n.t('teamMgmt.addFailed');
          this.toast.error(msg);
        },
      });
  }

  removeMember(member: TeamMember): void {
    const team = this.selectedTeam();
    if (!team) return;
    this.teamService.removeMember(team.id, member.id).subscribe({
      next: () => {
        this.teamMembers.update((ms) => ms.filter((m) => m.id !== member.id));
        this.toast.success(this.i18n.t('teamMgmt.memberRemoved'));
      },
    });
  }

  deleteTeam(team: Team): void {
    this.confirmDeleteTeam.set(team);
  }

  doDeleteTeam(): void {
    const team = this.confirmDeleteTeam();
    if (!team) return;
    this.teamService.delete(team.id).subscribe({
      next: () => {
        this.teams.update((ts) => ts.filter((t) => t.id !== team.id));
        if (this.selectedTeam()?.id === team.id) {
          this.selectedTeam.set(null);
        }
        this.confirmDeleteTeam.set(null);
        this.toast.success(this.i18n.t('teamMgmt.deleted'));
      },
    });
  }

  closeDetail(): void {
    this.selectedTeam.set(null);
  }
}
