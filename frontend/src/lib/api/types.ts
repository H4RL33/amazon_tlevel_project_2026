export interface UserResponse {
  id: number;
  cognito_sub: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

export interface TopicResponse {
  id: number;
  slug: string;
  name: string;
  description: string;
  accent_colour: string;
}

export interface TLevelResponse {
  id: number;
  topic_id: number;
  name: string;
  entry_requirements: string;
  how_to_apply: string;
}

export interface TopicDetailResponse extends TopicResponse {
  t_levels: TLevelResponse[];
}

export type ContentType = 'article' | 'audio' | 'video';

export interface TagResponse {
  id: number;
  name: string;
}

export interface ContentListResponse {
  id: number;
  title: string;
  content_type: ContentType;
  topic_id: number;
  t_level_id: number | null;
  tags: TagResponse[];
  created_at: string;
}

export interface ContentDetailResponse extends ContentListResponse {
  body: string | null;
  media_url: string | null;
}

export interface ProgressResponse {
  content_id: number;
  last_viewed_at: string;
  progress_pct: number;
  content: ContentListResponse;
}
