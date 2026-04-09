import { Routes } from '@angular/router';

import { MemberDetailComponent } from './member-detail/member-detail.component';
import { MemberListComponent } from './member-list/member-list.component';

export const routes: Routes = [
  { path: '', component: MemberListComponent },
  { path: 'members/:id', component: MemberDetailComponent },
  { path: '**', redirectTo: '' },
];
