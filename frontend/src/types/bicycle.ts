// Bicycle types for frontend

export type BicycleCondition = "NEW" | "USED";
export type BicycleStatus = "AVAILABLE" | "RESERVED" | "SOLD" | "MAINTENANCE";

export interface Bicycle {
  id: string;
  title: string;
  brand: string;
  model: string;
  year: number;
  condition: BicycleCondition;
  license_plate?: string;
  cash_price: number;
  hire_purchase_price: number;
  mileage_km?: number;
  description?: string;
  branch_id: string;
  branch_name?: string;
  status: BicycleStatus;
  image_urls: string[];
  thumbnail_url?: string;
  created_at: string;
  monthly_payment_estimate?: number;
}

export interface BicycleListResponse {
  data: Bicycle[];
  total: number;
  offset: number;
  limit: number;
}

export interface Branch {
  id: string;
  name: string;
  allows_bicycle_sales: boolean;
  bicycle_display_order: number;
  map_coordinates?: {
    lat: number;
    lng: number;
  };
  operating_hours?: string;
  public_description?: string;
}

export interface BicycleApplication {
  full_name: string;
  phone: string;
  email?: string;
  nip_number?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  employer_name?: string;
  monthly_income?: number;
  bicycle_id: string;
  branch_id: string;
  tenure_months: 12 | 24 | 36 | 48;
  down_payment: number;
}

export type ApplicationStatus = "PENDING" | "UNDER_REVIEW" | "APPROVED" | "REJECTED" | "CONVERTED_TO_LOAN";

export interface ApplicationResponse {
  id: string;
  full_name: string;
  phone: string;
  email?: string;
  nip_number?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  employer_name?: string;
  monthly_income?: number;
  bicycle_id: string;
  branch_id: string;
  tenure_months: number;
  down_payment: number;
  status: ApplicationStatus;
  notes?: string;
  loan_id?: string;
  submitted_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
}
