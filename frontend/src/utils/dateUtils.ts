/**
 * Utility functions for handling dates and timestamps
 */

/**
 * Format UTC timestamp to local time string
 * @param utcTimestamp - ISO string timestamp in UTC
 * @returns Formatted local time string
 */
export const formatDateToLocal = (utcTimestamp: string): string => {
  if (!utcTimestamp) return '-';
  
  // Parse the timestamp as UTC and convert to local time
  // Note: Date constructor automatically handles UTC string format
  const date = new Date(utcTimestamp);
  
  // Ensure the date was parsed correctly
  if (isNaN(date.getTime())) {
    return 'Invalid date';
  }
  
  // Return formatted local time
  return date.toLocaleString();
};

/**
 * Format UTC timestamp to local date only (no time)
 * @param utcTimestamp - ISO string timestamp in UTC
 * @returns Formatted local date string
 */
export const formatDateOnly = (utcTimestamp: string): string => {
  if (!utcTimestamp) return '-';
  
  const date = new Date(utcTimestamp);
  
  if (isNaN(date.getTime())) {
    return 'Invalid date';
  }
  
  return date.toLocaleDateString();
};

/**
 * Format UTC timestamp to local time only (no date)
 * @param utcTimestamp - ISO string timestamp in UTC
 * @returns Formatted local time string
 */
export const formatTimeOnly = (utcTimestamp: string): string => {
  if (!utcTimestamp) return '-';
  
  const date = new Date(utcTimestamp);
  
  if (isNaN(date.getTime())) {
    return 'Invalid time';
  }
  
  return date.toLocaleTimeString();
};

/**
 * Get current timestamp in UTC format for API calls
 * @returns UTC timestamp string
 */
export const getCurrentUTCTimestamp = (): string => {
  return new Date().toISOString();
};

// Default export for easier importing
export default {
  formatDateToLocal,
  formatDateOnly,
  formatTimeOnly,
  getCurrentUTCTimestamp
};