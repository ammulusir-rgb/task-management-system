import {
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TitleCasePipe } from '@angular/common';
import { UserManagementService } from '@core/services/user-management.service';
import { TranslationService } from '@core/services/translation.service';
import { User } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';
import { ConfirmDialogComponent } from '@shared/components/confirm-dialog/confirm-dialog.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    TitleCasePipe,
    LoadingSpinnerComponent,
    UserAvatarComponent,
    ConfirmDialogComponent,
    TranslatePipe,
  ],
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.scss'],
})
export class UserManagementComponent implements OnInit {
  private userService = inject(UserManagementService);
  private toast = inject(ToastService);
  i18n = inject(TranslationService);

  loading = signal(true);
  users = signal<User[]>([]);
  confirmDelete = signal<User | null>(null);

  // Create user form
  showCreate = false;
  newUser = {
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    role: 'member',
    job_title: '',
  };

  // Filters
  searchQuery = '';
  roleFilter = '';

  // Edit
  editingUser = signal<User | null>(null);
  editForm: { first_name: string; last_name: string; role: 'admin' | 'manager' | 'member'; job_title: string; is_active: boolean } = {
    first_name: '',
    last_name: '',
    role: 'member',
    job_title: '',
    is_active: true,
  };

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers(): void {
    this.loading.set(true);
    const params: any = {};
    if (this.searchQuery) params.search = this.searchQuery;
    if (this.roleFilter) params.role = this.roleFilter;
    this.userService.list(params).subscribe({
      next: (res) => {
        this.users.set(res.results);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  createUser(): void {
    this.userService.create(this.newUser).subscribe({
      next: () => {
        this.toast.success(this.i18n.t('userMgmt.created'));
        this.showCreate = false;
        this.resetNewUser();
        this.loadUsers();
      },
      error: (err) => {
        const msg = err?.error?.email?.[0] || err?.error?.detail || this.i18n.t('userMgmt.createFailed');
        this.toast.error(msg);
      },
    });
  }

  startEdit(user: User): void {
    this.editingUser.set(user);
    this.editForm = {
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      job_title: user.job_title,
      is_active: user.is_active,
    };
  }

  saveEdit(): void {
    const user = this.editingUser();
    if (!user) return;
    this.userService.update(user.id, this.editForm).subscribe({
      next: (updated) => {
        this.users.update((list) =>
          list.map((u) => (u.id === updated.id ? updated : u))
        );
        this.editingUser.set(null);
        this.toast.success(this.i18n.t('userMgmt.updated'));
      },
      error: () => this.toast.error(this.i18n.t('userMgmt.updateFailed')),
    });
  }

  cancelEdit(): void {
    this.editingUser.set(null);
  }

  deleteUser(user: User): void {
    this.confirmDelete.set(user);
  }

  doDelete(): void {
    const user = this.confirmDelete();
    if (!user) return;
    this.userService.delete(user.id).subscribe({
      next: () => {
        this.users.update((list) => list.filter((u) => u.id !== user.id));
        this.confirmDelete.set(null);
        this.toast.success(this.i18n.t('userMgmt.deleted'));
      },
      error: () => this.toast.error(this.i18n.t('userMgmt.deleteFailed')),
    });
  }

  onSearch(): void {
    this.loadUsers();
  }

  onRoleFilter(role: string): void {
    this.roleFilter = role;
    this.loadUsers();
  }

  private resetNewUser(): void {
    this.newUser = {
      email: '',
      first_name: '',
      last_name: '',
      password: '',
      role: 'member',
      job_title: '',
    };
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString(this.i18n.getLocale(), {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }
}
