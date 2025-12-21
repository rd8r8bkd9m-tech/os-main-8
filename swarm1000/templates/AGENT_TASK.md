# Agent Task: {{task_id}}

## Task Information

**Area**: {{area}}  
**Priority**: {{priority}}/10  
**Estimated Time**: {{estimated_minutes}} minutes  
**Risk Level**: {{risk}}  
**Assigned To**: {{assigned_to}}  

## Description

{{description}}

## Inputs

{{#each inputs}}
- {{this}}
{{/each}}

## Expected Outputs

{{#each expected_outputs}}
- {{this}}
{{/each}}

## Tests Required

{{#each tests}}
- {{this}}
{{/each}}

## Definition of Done

{{#each definition_of_done}}
- [ ] {{this}}
{{/each}}

## Dependencies

{{#if deps}}
This task depends on:
{{#each deps}}
- {{this}}
{{/each}}
{{else}}
No dependencies - can start immediately
{{/if}}

## Implementation Guidelines

1. Follow Kolibri AI coding standards
2. Write type-safe, energy-efficient code
3. Add comprehensive tests
4. Update documentation
5. Ensure security best practices

## Quality Checklist

- [ ] Code follows style guide
- [ ] All tests pass
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance acceptable
- [ ] Accessibility considerations addressed

## Submission

When complete:
1. Commit changes to your worker branch
2. Run quality gate checks
3. Submit for review
4. Address reviewer feedback
