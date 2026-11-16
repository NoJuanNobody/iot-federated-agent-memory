import type { Skill } from '../skills.js';
import { findSkill } from '../skills.js';
import type { Tool } from './index.js';

export function makeUseSkillTool(skills: Skill[]): Tool {
  return {
    name: 'use_skill',
    description:
      'Load the full instructions for a skill listed in the system prompt. ' +
      'Call this BEFORE attempting a task a skill covers, then follow the instructions it returns.',
    parameters: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: 'Skill name exactly as listed in the system prompt.',
          enum: skills.length > 0 ? skills.map((s) => s.name) : undefined,
        },
      },
      required: ['name'],
    },
    needsApproval: false,
    summarize: (args) => String(args.name ?? ''),
    async run(args) {
      const skill = findSkill(skills, String(args.name ?? ''));
      if (!skill) {
        const available = skills.map((s) => s.name).join(', ') || '(none)';
        throw new Error(`Unknown skill. Available skills: ${available}`);
      }
      return [
        `# Skill: ${skill.name}`,
        `Skill files live in: ${skill.dir}`,
        '',
        skill.body,
      ].join('\n');
    },
  };
}
