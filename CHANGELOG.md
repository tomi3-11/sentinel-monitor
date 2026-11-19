# Changelog

## [0.1.5] - 2026-11-18

### Fixed
- Remove duplicate TLS validation errors from CLI output.
- Distinguish HTTP reachability failures from HTTP error responses.

### Improved
- Display one uninterrupted status row per monitored site.
- Move request, TLS validation, and SSL metadata errors into a
  separate Diagnostics section grouped by site.
- Omit the Diagnostics section when no diagnostics are present.

## [0.1.4] - 2026-11-15

### Added
- X.509 certificate inspection using cryptography.
- TLS integration tests covering valid, expired, untrusted,
  and hostname-mismatched certificates.

### Improved
- Separate certificate metadata retrieval from TLS validation.
- Preserve certificate validation failures while retrieving
  expiry metadata.
- Report HTTP reachability, certificate metadata, and
  certificate validation independently.

### Dependencies
- Add cryptography 46.0.4 for X.509 certificate parsing.
