/**
 * Data service for v2/data exam routing
 * Provides aliases, contract references, and data loading functions.
 */

// Legacy ID → canonical examId aliases
const EXAM_ID_ALIASES = {
  'calc-bc-2015-intl': 'calc-bc-2015-intl',
  'calc-bc-2016-intl': 'calc-bc-2016-intl',
  'calc-bc-2017-intl': 'calc-bc-2017-intl',
  'calc-bc-2018-intl': 'calc-bc-2018-intl',
  'physics-c-mech-2018-intl': 'physics-c-mech-2018-intl',
  '2018Intl_MECH': 'physics-c-mech-2018-intl',
  'physics-c-em-2018-intl': 'physics-c-em-2018-intl',
  'physics-c-mech-2017-intl': 'physics-c-mech-2017-intl',
  '2017Intl_MECH': 'physics-c-mech-2017-intl',
  'physics-c-em-2017-intl': 'physics-c-em-2017-intl',
  '2017Intl_EM': 'physics-c-em-2017-intl',
  'microeconomics-2017-intl': 'microeconomics-2017-intl',
  '1902622410416164864': 'microeconomics-2017-intl',
  'microeconomics-2018-intl': 'microeconomics-2018-intl',
  '1902622410881732608': 'microeconomics-2018-intl',
  'microeconomics-2019-intl': 'microeconomics-2019-intl',
  '1902622418683138048': 'microeconomics-2019-intl',
  'microeconomics-2021-intl': 'microeconomics-2021-intl',
  '1902622419140317184': 'microeconomics-2021-intl',
  '1902622411338911744': 'calc-bc-2017-intl',
  '1902622411800285184': 'calc-bc-2018-intl',
  '2015Intl': 'calc-bc-2015-intl',
  '2016Intl': 'calc-bc-2016-intl',
  '2017Intl': 'calc-bc-2017-intl',
  '2018Intl': 'calc-bc-2018-intl',
  'statistics-2017-intl': 'statistics-2017-intl',
  'statistics-2018-intl': 'statistics-2018-intl',
  '1902622413633196032': 'statistics-2018-intl',
  'statistics-2021-na': 'statistics-2021-na',
  'statistics-2022-na': 'statistics-2022-na',
  'statistics-2023-na': 'statistics-2023-na',
  'statistics-2024-intl': 'statistics-2024-intl',
  'statistics-2024-na': 'statistics-2024-na',
  'statistics-2025-intl': 'statistics-2025-intl',
  'statistics-2025-na': 'statistics-2025-na'
};

// Subject → trunk contract path mapping
const EXAM_BRANCH_CONTRACTS = {
  'ap_calculus_bc': 'v2/data/contracts/ap-calculus-bc-trunk-contract.json',
  'ap_physics_c_mechanics': 'v2/data/contracts/ap-physics-c-mechanics-trunk-contract.json',
  'ap_physics_c_electricity_magnetism': 'v2/data/contracts/ap-physics-c-electricity-magnetism-trunk-contract.json',
  'ap_microeconomics': 'v2/data/contracts/ap-microeconomics-trunk-contract.json',
  'ap_statistics': 'v2/data/contracts/ap-statistics-trunk-contract.json'
};

// subjectSlug lookup by examId prefix
function getSubjectSlug(examId) {
  if (examId.startsWith('calc-bc-')) return 'ap_calculus_bc';
  if (examId.startsWith('physics-c-mech-')) return 'ap_physics_c_mechanics';
  if (examId.startsWith('physics-c-em-')) return 'ap_physics_c_electricity_magnetism';
  if (examId.startsWith('microeconomics-')) return 'ap_microeconomics';
  if (examId.startsWith('statistics-')) return 'ap_statistics';
  return null;
}

/**
 * Resolve raw examId to canonical examId using aliases.
 */
function resolveExamId(rawId) {
  return EXAM_ID_ALIASES[rawId] || rawId;
}

/**
 * Load exam data (questions.json) for a given examId.
 * Returns parsed JSON or null on failure.
 */
function loadExamData(examId) {
  const canonical = resolveExamId(examId);
  const url = `v2/data/${canonical}/questions.json`;

  if (typeof fetch !== 'undefined') {
    return fetch(url)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }

  // Node.js fallback
  try {
    const fs = require('fs');
    const path = require('path');
    const filePath = path.resolve(__dirname, '..', '..', 'v2', 'data', canonical, 'questions.json');
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

/**
 * Load branch mapping (question-branch-mapping.json) for a given examId.
 * Returns parsed JSON or null on failure.
 */
function loadBranchMapping(examId) {
  const canonical = resolveExamId(examId);
  const url = `v2/data/${canonical}/question-branch-mapping.json`;

  if (typeof fetch !== 'undefined') {
    return fetch(url)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }

  // Node.js fallback
  try {
    const fs = require('fs');
    const path = require('path');
    const filePath = path.resolve(__dirname, '..', '..', 'v2', 'data', canonical, 'question-branch-mapping.json');
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

/**
 * Load trunk contract for a subject.
 */
function loadTrunkContract(subjectSlug) {
  const contractPath = EXAM_BRANCH_CONTRACTS[subjectSlug];
  if (!contractPath) return null;

  const url = contractPath;

  if (typeof fetch !== 'undefined') {
    return fetch(url)
      .then(r => r.ok ? r.json() : null)
      .catch(() => null);
  }

  // Node.js fallback
  try {
    const fs = require('fs');
    const path = require('path');
    const filePath = path.resolve(__dirname, '..', '..', contractPath.replace(/\//g, path.sep));
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    EXAM_ID_ALIASES,
    EXAM_BRANCH_CONTRACTS,
    resolveExamId,
    getSubjectSlug,
    loadExamData,
    loadBranchMapping,
    loadTrunkContract
  };
} else if (typeof window !== 'undefined') {
  window.DataService = {
    EXAM_ID_ALIASES,
    EXAM_BRANCH_CONTRACTS,
    resolveExamId,
    getSubjectSlug,
    loadExamData,
    loadBranchMapping,
    loadTrunkContract
  };
}
