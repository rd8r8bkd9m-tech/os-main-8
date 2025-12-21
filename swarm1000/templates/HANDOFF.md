# Task Handoff

## From Agent

**ID**: {{from_agent_id}}  
**Role**: {{from_agent_role}}  
**Date**: {{handoff_date}}  

## To Agent

**ID**: {{to_agent_id}}  
**Role**: {{to_agent_role}}  

## Task

**ID**: {{task_id}}  
**Title**: {{task_title}}  
**Status**: {{task_status}}  

## Work Completed

{{work_completed}}

## Remaining Work

{{remaining_work}}

## Blockers / Issues

{{#if blockers}}
{{blockers}}
{{else}}
None identified
{{/if}}

## Context & Notes

{{context}}

## Files Modified

{{#each files_modified}}
- `{{this}}`
{{/each}}

## Next Steps

1. {{next_step_1}}
2. {{next_step_2}}
3. {{next_step_3}}

## Questions for Next Agent

{{questions}}

---

**Handoff Protocol**: This task is being transferred as part of the Kolibri Swarm-1000 orchestration. Please review all context before continuing work.
