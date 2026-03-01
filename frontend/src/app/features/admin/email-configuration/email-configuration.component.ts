import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { NgClass, TitleCasePipe } from '@angular/common';
import { EmailService } from '@core/services/email.service';
import { ProjectService } from '@core/services/project.service';
import { TranslationService } from '@core/services/translation.service';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';
import { EmailConfiguration, EmailRule, Project, User } from '@models/index';

@Component({
  selector: 'app-email-configuration',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    NgClass,
    TitleCasePipe,
    LoadingSpinnerComponent,
    TranslatePipe,
  ],
  templateUrl: './email-configuration.component.html',
  styleUrls: ['./email-configuration.component.scss'],
})
export class EmailConfigurationComponent implements OnInit {
  private fb = inject(FormBuilder);
  private emailService = inject(EmailService);
  private projectService = inject(ProjectService);
  private toast = inject(ToastService);
  i18n = inject(TranslationService);

  loading = signal(true);
  saving = signal(false);
  testing = signal(false);
  config = signal<EmailConfiguration | null>(null);
  projects = signal<Project[]>([]);
  rules = signal<EmailRule[]>([]);
  
  // Form states
  showImapForm = signal(false);
  showSmtpForm = signal(false);
  showRuleForm = signal(false);
  editingRule = signal<EmailRule | null>(null);

  configForm = this.fb.nonNullable.group({
    imap_enabled: [false],
    imap_host: ['', [Validators.required]],
    imap_port: [993, [Validators.required, Validators.min(1)]],
    imap_use_ssl: [true],
    imap_username: ['', [Validators.required, Validators.email]],
    imap_password: [''],
    smtp_enabled: [false],
    smtp_host: ['', [Validators.required]],
    smtp_port: [587, [Validators.required, Validators.min(1)]],
    smtp_use_tls: [true],
    smtp_username: ['', [Validators.required, Validators.email]],
    smtp_password: [''],
    task_email_address: ['', [Validators.email]],
    default_project: [''],
    auto_assign_reporter: [true],
  });

  ruleForm = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    rule_type: ['subject_contains', [Validators.required]],
    rule_value: ['', [Validators.required]],
    is_active: [true],
    target_project: ['', [Validators.required]],
    default_assignee: [''],
    default_priority: ['medium'],
    default_status: ['todo'],
  });

  ruleTypes = [
    { value: 'subject_contains', label: 'Subject contains' },
    { value: 'sender_domain', label: 'Sender domain' },
    { value: 'sender_email', label: 'Sender email' },
    { value: 'body_contains', label: 'Body contains' },
  ];

  priorities = ['critical', 'high', 'medium', 'low'];
  statuses = ['backlog', 'todo', 'in_progress', 'in_review', 'done'];

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading.set(true);
    
    // Load projects first
    this.projectService.list().subscribe({
      next: (res) => {
        this.projects.set(res.results);
      }
    });

    // Load email configuration
    this.emailService.getConfiguration().subscribe({
      next: (config) => {
        this.config.set(config);
        if (config) {
          this.configForm.patchValue(config);
          this.loadRules();
        }
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      }
    });
  }

  loadRules(): void {
    this.emailService.getRules().subscribe({
      next: (rules) => {
        this.rules.set(rules);
      }
    });
  }

  saveConfiguration(): void {
    if (this.configForm.invalid) return;

    this.saving.set(true);
    const rawFormData = this.configForm.getRawValue();

    // Create proper form data object with optional password fields
    const formData: any = { ...rawFormData };
    
    // Only include password if it's changed
    if (!rawFormData.imap_password) {
      formData.imap_password = undefined;
    }
    if (!rawFormData.smtp_password) {
      formData.smtp_password = undefined;
    }

    const saveMethod = this.config() 
      ? this.emailService.updateConfiguration(this.config()!.id, formData)
      : this.emailService.createConfiguration(formData);

    saveMethod.subscribe({
      next: (config) => {
        this.config.set(config);
        this.saving.set(false);
        this.toast.success(this.i18n.t('emailConfig.saved'));
      },
      error: () => {
        this.saving.set(false);
        this.toast.error(this.i18n.t('emailConfig.saveFailed'));
      }
    });
  }

  testConnection(): void {
    if (!this.config()) return;

    this.testing.set(true);
    this.emailService.testConnection(this.config()!.id).subscribe({
      next: (result) => {
        this.testing.set(false);
        
        const messages = [];
        if (result.imap) messages.push('IMAP: ✓');
        if (result.smtp) messages.push('SMTP: ✓');
        if (result.errors?.length) {
          messages.push(...result.errors.map(err => `❌ ${err}`));
        }
        
        this.toast.info(messages.join('\n'));
      },
      error: () => {
        this.testing.set(false);
        this.toast.error(this.i18n.t('emailConfig.testFailed'));
      }
    });
  }

  processEmails(): void {
    if (!this.config()) return;

    this.emailService.processEmails(this.config()!.id).subscribe({
      next: () => {
        this.toast.success(this.i18n.t('emailConfig.processStarted'));
      },
      error: () => {
        this.toast.error(this.i18n.t('emailConfig.processFailed'));
      }
    });
  }

  // Rule Management
  openRuleForm(rule?: EmailRule): void {
    this.editingRule.set(rule || null);
    
    if (rule) {
      // Handle object fields properly for form
      const formValues = {
        ...rule,
        target_project: typeof rule.target_project === 'object' 
          ? rule.target_project?.id || '' 
          : rule.target_project || '',
        default_assignee: typeof rule.default_assignee === 'object'
          ? rule.default_assignee?.id || ''
          : rule.default_assignee || ''
      };
      this.ruleForm.patchValue(formValues);
    } else {
      this.ruleForm.reset({
        rule_type: 'subject_contains',
        is_active: true,
        default_priority: 'medium',
        default_status: 'todo'
      });
    }
    
    this.showRuleForm.set(true);
  }

  closeRuleForm(): void {
    this.showRuleForm.set(false);
    this.editingRule.set(null);
    this.ruleForm.reset();
  }

  saveRule(): void {
    if (this.ruleForm.invalid) return;

    const formData = this.ruleForm.getRawValue();
    const editingRule = this.editingRule();

    const saveMethod = editingRule
      ? this.emailService.updateRule(editingRule.id, formData)
      : this.emailService.createRule(formData);

    saveMethod.subscribe({
      next: () => {
        this.loadRules();
        this.closeRuleForm();
        this.toast.success(this.i18n.t('emailConfig.ruleSaved'));
      },
      error: () => {
        this.toast.error(this.i18n.t('emailConfig.ruleSaveFailed'));
      }
    });
  }

  deleteRule(rule: EmailRule): void {
    if (!confirm(this.i18n.t('emailConfig.confirmDeleteRule'))) return;

    this.emailService.deleteRule(rule.id).subscribe({
      next: () => {
        this.loadRules();
        this.toast.success(this.i18n.t('emailConfig.ruleDeleted'));
      },
      error: () => {
        this.toast.error(this.i18n.t('emailConfig.ruleDeleteFailed'));
      }
    });
  }
}
