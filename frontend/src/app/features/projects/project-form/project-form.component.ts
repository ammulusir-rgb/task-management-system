import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NgClass } from '@angular/common';
import { ProjectService } from '@core/services/project.service';
import { OrganizationService } from '@core/services/organization.service';
import { TranslationService } from '@core/services/translation.service';
import { Organization } from '@models/index';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';

@Component({
  selector: 'app-project-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, NgClass, TranslatePipe],
  templateUrl: './project-form.component.html',
  styleUrls: ['./project-form.component.scss'],
})
export class ProjectFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private projectService = inject(ProjectService);
  private orgService = inject(OrganizationService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    prefix: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(5)]],
    organization: ['', Validators.required],
    description: [''],
  });

  organizations = signal<Organization[]>([]);
  isEdit = signal(false);
  saving = signal(false);
  submitted = signal(false);
  private projectId = '';

  ngOnInit(): void {
    this.orgService.list().subscribe({
      next: (res) => this.organizations.set(res.results),
    });

    this.projectId = this.route.snapshot.params['projectId'];
    if (this.projectId) {
      this.isEdit.set(true);
      this.projectService.get(this.projectId).subscribe({
        next: (p) => {
          this.form.patchValue({
            name: p.name,
            prefix: p.prefix,
            organization: p.organization,
            description: p.description,
          });
        },
      });
    }
  }

  onSubmit(): void {
    this.submitted.set(true);
    if (this.form.invalid) return;

    this.saving.set(true);
    const data = this.form.getRawValue();

    const obs = this.isEdit()
      ? this.projectService.update(this.projectId, data)
      : this.projectService.create(data);

    obs.subscribe({
      next: (project) => {
        this.toast.success(
          this.isEdit() ? this.i18n.t('projectForm.updated') : this.i18n.t('projectForm.created')
        );
        this.router.navigate(['/projects', project.id]);
      },
      error: () => this.saving.set(false),
    });
  }
}
