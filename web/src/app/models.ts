export interface Party {
  id: number;
  name: string;
  abbreviation: string | null;
}

export interface MemberListItem {
  id: number;
  name_display_as: string;
  name_full_title: string;
  constituency: string | null;
  party: Party | null;
  interest_count: number;
}

export interface PaginatedMembers {
  items: MemberListItem[];
  total: number;
  skip: number;
  take: number;
}

export interface MemberDetail {
  id: number;
  name_list_as: string;
  name_display_as: string;
  name_full_title: string;
  name_address_as: string | null;
  gender: string;
  thumbnail_url: string | null;
  party: Party | null;
  constituency: string | null;
  house: number | null;
  membership_start_date: string | null;
  status_description: string | null;
}

export interface RegisteredInterest {
  interest_id: number;
  category_name: string;
  parent_interest_id: number | null;
  interest_text: string;
  created_when: string | null;
}
