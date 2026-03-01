import {
  Component,
  inject,
  OnInit,
  OnDestroy,
  signal,
  computed,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  CdkDragDrop,
  CdkDrag,
  CdkDropList,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';
import { ProjectService } from '@core/services/project.service';
import { TaskService } from '@core/services/task.service';
import { WebSocketService } from '@core/services/websocket.service';
import { TranslationService } from '@core/services/translation.service';
import { Board, Column, TaskListItem } from '@models/index';
import { LoadingSpinnerComponent } from '@shared/components/loading-spinner/loading-spinner.component';
import { PriorityBadgeComponent } from '@shared/components/priority-badge/priority-badge.component';
import { UserAvatarComponent } from '@shared/components/user-avatar/user-avatar.component';
import { TranslatePipe } from '@shared/pipes/translate.pipe';
import { ToastService } from '@shared/services/toast.service';
import { TasksByColumn } from './board.types';

@Component({
  selector: 'app-board',
  standalone: true,
  imports: [
    RouterLink,
    CdkDrag,
    CdkDropList,
    LoadingSpinnerComponent,
    PriorityBadgeComponent,
    UserAvatarComponent,
    TranslatePipe,
  ],
  templateUrl: './board.component.html',
  styleUrls: ['./board.component.scss'],
})
export class BoardComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private projectService = inject(ProjectService);
  private taskService = inject(TaskService);
  private wsService = inject(WebSocketService);
  private toast = inject(ToastService);
  private i18n = inject(TranslationService);

  loading = signal(true);
  board = signal<Board | null>(null);
  tasksByColumn = signal<TasksByColumn>({});

  connectedDropLists = computed(() =>
    (this.board()?.columns ?? []).map((c) => 'column-' + c.id)
  );

  ngOnInit(): void {
    const boardId = this.route.snapshot.params['boardId'];
    this.loadBoard(boardId);
    this.connectWebSocket(boardId);
  }

  ngOnDestroy(): void {
    this.wsService.disconnect('board');
  }

  private loadBoard(boardId: string): void {
    this.projectService.getBoard(boardId).subscribe({
      next: (board) => {
        this.board.set(board);
        this.loadTasks(board);
      },
      error: () => this.loading.set(false),
    });
  }

  private loadTasks(board: Board): void {
    this.taskService
      .list({ board: board.id, page_size: 200, ordering: 'position' })
      .subscribe({
        next: (res) => {
          const grouped: TasksByColumn = {};
          for (const col of board.columns) {
            grouped[col.id] = [];
          }
          for (const task of res.results) {
            if (grouped[task.column]) {
              grouped[task.column].push(task);
            }
          }
          this.tasksByColumn.set(grouped);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  getColumnTasks(columnId: string): TaskListItem[] {
    return this.tasksByColumn()[columnId] ?? [];
  }

  onTaskDrop(event: CdkDragDrop<TaskListItem[]>, targetColumn: Column): void {
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );
    }

    this.tasksByColumn.update((prev) => ({ ...prev }));

    const task = event.container.data[event.currentIndex];
    this.taskService
      .move(task.id, {
        column_id: targetColumn.id,
        position: event.currentIndex,
      })
      .subscribe({
        error: () => this.toast.error(this.i18n.t('board.moveError')),
      });
  }

  addColumn(): void {
    const name = prompt(this.i18n.t('board.columnNamePrompt'));
    if (!name || !this.board()) return;

    this.projectService
      .createColumn({
        name,
        board: this.board()!.id,
        position: this.board()!.columns.length,
      })
      .subscribe({
        next: (col) => {
          this.board.update((b) =>
            b ? { ...b, columns: [...b.columns, col] } : b
          );
          this.tasksByColumn.update((prev) => ({ ...prev, [col.id]: [] }));
          this.toast.success(this.i18n.t('board.columnAdded'));
        },
      });
  }

  isOverdue(dateStr: string): boolean {
    return new Date(dateStr) < new Date();
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString(this.i18n.getLocale(), {
      month: 'short',
      day: 'numeric',
    });
  }

  private connectWebSocket(boardId: string): void {
    const ws = this.wsService.connect('board', `board/${boardId}/`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'task_update') {
        this.loadBoard(boardId);
      }
    };
  }
}
