export interface CalendarEvent {
  id: string;
  title: string;
  startDatetime: number;
  endDatetime: number;
  location: Location;
}

export interface Location {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
}