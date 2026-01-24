# Telegram Signal Extraction System - Documentation

This directory contains comprehensive documentation for the Telegram Signal Extraction System project.

## Documentation Overview

### 1. [Requirements](requirements.md)
**Purpose**: Defines what the system should do

**Contents**:
- Functional requirements (channel monitoring, signal extraction, data storage)
- Non-functional requirements (performance, reliability, security)
- User stories
- Constraints and assumptions
- Future enhancements

**Audience**: Stakeholders, developers, testers

### 2. [Technical Specifications](technical-specifications.md)
**Purpose**: Describes how the system will be built

**Contents**:
- System architecture overview
- Technology stack (Python, Telethon, etc.)
- Component specifications (TelegramListener, SignalExtractor, CSVWriter)
- Data models and structures
- API integration details
- Error handling strategy
- Testing approach

**Audience**: Developers, architects

### 3. [Architecture](architecture.md)
**Purpose**: Detailed system design and component interactions

**Contents**:
- High-level architecture diagram
- Component layer breakdown (Application, Business Logic, Data Access, Infrastructure)
- Data flow diagrams (normal flow, error flow, recovery flow)
- Deployment architecture
- Security architecture
- Scalability considerations
- Monitoring and observability

**Audience**: Developers, system architects, DevOps

### 4. [Data Format Specification](data-format.md)
**Purpose**: Defines all data formats used in the system

**Contents**:
- CSV output format (schema, field specifications)
- Symbol normalization rules
- Error log format (JSONL)
- System log format
- Configuration file structure (config.yaml, .env)
- MT5 integration specifications
- Example message formats and expected outputs

**Audience**: Developers, MT5 EA developers, data analysts

### 5. [Signal Formats](signal-formats.md)
**Purpose**: Documents actual signal formats from channels and extraction patterns

**Contents**:
- Nick Alpha Trader format analysis (based on real screenshots)
- Extraction rules and regex patterns
- Symbol normalization mappings
- Common pattern variations
- Confidence scoring algorithm
- Validation rules
- Test cases and edge cases
- Pattern priority and learning strategy

**Audience**: Developers implementing extraction logic

### 6. [Implementation Roadmap](implementation-roadmap.md)
**Purpose**: Step-by-step guide to building the system

**Contents**:
- 8-phase implementation plan (7-8 weeks to production)
- Detailed tasks for each phase
- Code deliverables and structure
- Testing strategies and success criteria
- Risk management
- Timeline and milestones
- Best practices and maintenance procedures

**Audience**: Project managers, developers

## Quick Start Guide

### For Developers Starting Implementation

1. **Read in this order**:
   - [Requirements](requirements.md) - Understand what we're building
   - [Signal Formats](signal-formats.md) - See real examples of signals
   - [Implementation Roadmap](implementation-roadmap.md) - Follow the step-by-step plan
   - [Technical Specifications](technical-specifications.md) - Reference during implementation
   - [Data Format Specification](data-format.md) - Reference when building CSV writer

2. **Start with Phase 1** of the Implementation Roadmap:
   - Set up project structure
   - Get Telegram API credentials
   - Initialize development environment

3. **Reference Architecture** when:
   - Designing component interactions
   - Implementing error handling
   - Planning deployment

### For MT5 EA Developers

1. **Read**: [Data Format Specification](data-format.md)
   - Focus on "CSV Output Format" section
   - Review "MT5 Integration Specification" section
   - Check example outputs

2. **Key Information**:
   - CSV schema and field types
   - File access patterns
   - Processing workflow

### For Stakeholders

1. **Read**: [Requirements](requirements.md)
   - Functional capabilities
   - Success criteria
   - Timeline expectations (from Implementation Roadmap)

2. **High-level Overview**: [Architecture](architecture.md)
   - System overview diagram
   - Deployment architecture

## Project Context

### Problem Statement
Manual monitoring of Telegram trading signal channels is time-consuming and error-prone. Traders need an automated system to extract signals and feed them to MT5 Expert Advisors for execution.

### Solution
A Python-based system that:
1. Monitors Telegram channels 24/7
2. Extracts trading signals using pattern matching
3. Saves signals to CSV files
4. Provides structured data for MT5 EA consumption

### Target Channels (Initial)
- https://t.me/nickalphatrader
- https://t.me/GaryGoldLegacy

### Timeline
- MVP: 6-7 weeks
- Production Ready: 7-8 weeks

## Key Design Decisions

### Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.9+ | Best Telegram library support, easy MT5 integration |
| Telegram Library | Telethon | Mature, stable, well-documented |
| Data Format | CSV | MT5 compatibility, simplicity |
| Configuration | YAML + .env | Human-readable, secure credential management |
| Extraction | Regex patterns | Fast, deterministic, easy to update |

### Architectural Patterns

- **Event-driven**: React to Telegram messages as they arrive
- **Layered architecture**: Separation of concerns (business logic, data access, infrastructure)
- **Fail-safe**: Continue processing on individual extraction failures
- **Atomic operations**: Prevent data corruption during writes

## Success Metrics

### Technical Metrics
- Extraction accuracy: >95%
- System uptime: >99.5%
- Message processing latency: <5 seconds
- Zero data loss

### Business Metrics
- Successful automation of 2+ channels
- Reduced manual signal entry time by >90%
- Improved trade execution speed

## Common Questions

### Q: What happens if the extraction fails?
**A**: The system logs the message to `extraction_errors.log` for manual review and continues processing other messages. No signals are lost.

### Q: How does the system handle network interruptions?
**A**: Automatic reconnection with exponential backoff. The system will retry up to 5 times before alerting.

### Q: Can I add more channels later?
**A**: Yes, simply add the channel to `config.yaml` without code changes.

### Q: How do I know if the system is working?
**A**: Monitor `logs/system.log` for activity. Check that `output/signals.csv` is being updated with new signals.

### Q: What if a channel changes its signal format?
**A**: Update the extraction patterns in the code. The system is designed for easy pattern updates. See [Signal Formats](signal-formats.md) for details.

## Document Maintenance

### When to Update

| Document | Update When... |
|----------|---------------|
| Requirements | New features added, requirements change |
| Technical Specs | Technology choices change, major refactoring |
| Architecture | System design changes, new components added |
| Data Format | CSV schema changes, new fields added |
| Signal Formats | New channels added, format changes observed |
| Roadmap | Phases completed, timeline adjusted |

### Version History

- **v1.0** (2026-01-24): Initial documentation created during planning phase

## Contributing

When updating documentation:
1. Keep it synchronized with code changes
2. Update examples when behavior changes
3. Add new sections as needed
4. Maintain clarity and accuracy
5. Review for technical accuracy

## Additional Resources

### External Documentation
- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram API Documentation](https://core.telegram.org/api)
- [MT5 MQL5 Documentation](https://www.mql5.com/en/docs)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

### Code Repository
- Main repo: [To be determined]
- Issue tracker: [To be determined]

## Support

For questions or issues:
1. Check relevant documentation section
2. Review error logs
3. Consult Implementation Roadmap for guidance
4. Refer to troubleshooting section (to be added)

---

**Last Updated**: 2026-01-24
**Version**: 1.0
**Status**: Planning Phase
