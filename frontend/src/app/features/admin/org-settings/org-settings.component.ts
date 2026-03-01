import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { OrganizationService } from '@core/services/organization.service';
import { TranslationService } from '@core/services/translation.service';
import { Organization } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-org-settings',
  standalone: true,
  imports: [FormsModule, RouterLink, LoadingSpinnerComponent, TranslatePipe],
  templateUrl: './org-settings.component.html',
  styleUrls: ['./org-settings.component.scss'],
})
export class OrgSettingsComponent implements OnInit {
  private orgService = inject(OrganizationService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  saving = signal(false);
  org = signal<Organization | null>(null);

  name = '';
  description = '';
  newOrgName = '';
  newOrgDescription = '';

  ngOnInit(): void {
    this.orgService.list().subscribe({
      next: (res) => {
        const org = res.results[0];
        if (org) {
          this.org.set(org);
          this.name = org.name;
          this.description = org.description ?? '';
        }
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  save(): void {
    if (!this.org()) return;
    this.saving.set(true);
    this.orgService
      .update(this.org()!.id, { name: this.name, description: this.description })
      .subscribe({
        next: (updated) => {
          this.org.set(updated);
          this.saving.set(false);
          this.toast.success(this.i18n.t('admin.settingsSaved'));
        },
        error: () => {
          this.saving.set(false);
          this.toast.error(this.i18n.t('admin.saveFailed'));
        },
      });
  }

  createOrg(): void {
    const name = this.newOrgName.trim();
    if (!name) return;
    this.saving.set(true);
    this.orgService
      .create({ name, description: this.newOrgDescription.trim() || undefined })
      .subscribe({
        next: (created) => {
          this.org.set(created);
          this.name = created.name;
          this.description = created.description ?? '';
          this.saving.set(false);
          this.toast.success(this.i18n.t('admin.orgCreated'));
        },
        error: () => {
          this.saving.set(false);
          this.toast.error(this.i18n.t('admin.orgCreateFailed'));
        },
      });
  }
}
