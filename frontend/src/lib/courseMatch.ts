import type { Course, WeekPlan } from './types'

const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()

/**
 * Resolve one resource title from a weekly plan entry back to a course card.
 * The LLM is told to copy titles verbatim, but it still paraphrases sometimes,
 * so we fall back through progressively looser matches.
 */
function resolveResource(
  resource: string | null | undefined,
  courses: Course[],
  excludedUrls = new Set<string>(),
): Course | undefined {
  if (!resource) return undefined
  const raw = resource.trim()
  if (!raw) return undefined

  // 1. exact, then case-insensitive
  let hit = courses.find(c => c.title === raw && !excludedUrls.has(c.url))
  if (hit) return hit
  hit = courses.find(c => c.title.toLowerCase() === raw.toLowerCase() && !excludedUrls.has(c.url))
  if (hit) return hit

  // 2. normalized equality (punctuation / spacing differences only)
  const target = norm(raw)
  if (!target) return undefined
  hit = courses.find(c => norm(c.title) === target && !excludedUrls.has(c.url))
  if (hit) return hit

  // 3. containment, but only when the shorter side is substantial enough that
  //    the match isn't accidental (a title like "R" must not match everything).
  hit = courses.find(c => {
    if (excludedUrls.has(c.url)) return false
    const t = norm(c.title)
    if (!t) return false
    const shorter = Math.min(t.length, target.length)
    if (shorter < 8) return false
    return t.includes(target) || target.includes(t)
  })
  if (hit) return hit

  // 4. strongest token overlap (>= 60% of the resource's words appear in the title)
  const words = target.split(' ').filter(w => w.length > 3)
  if (words.length) {
    let best: Course | undefined
    let bestRatio = 0
    for (const c of courses) {
      if (excludedUrls.has(c.url)) continue
      const t = norm(c.title)
      const ratio = words.filter(w => t.includes(w)).length / words.length
      if (ratio > bestRatio) {
        bestRatio = ratio
        best = c
      }
    }
    if (best && bestRatio >= 0.6) return best
  }

  return undefined
}

export type WeekCourse = {
  course: Course
  role: 'primary' | 'secondary'
  /** the plan's title text, kept so unresolved resources can still be shown */
  resourceTitle: string
}

/**
 * Every course a week refers to — the primary resource AND the secondary one.
 *
 * The old implementation only ever resolved `primary_resource`, which is why a
 * week listing two resources still expanded to a single card.
 */
export function findCoursesForWeek(
  weekPlan: WeekPlan,
  courses: Course[],
  weeklyPlan: WeekPlan[],
): WeekCourse[] {
  const out: WeekCourse[] = []
  const takenUrls = new Set<string>()

  const push = (course: Course | undefined, role: 'primary' | 'secondary', resourceTitle: string) => {
    if (!course || takenUrls.has(course.url)) return
    takenUrls.add(course.url)
    out.push({ course, role, resourceTitle })
  }

  push(resolveResource(weekPlan.primary_resource, courses), 'primary', weekPlan.primary_resource)
  if (weekPlan.secondary_resource) {
    push(
      resolveResource(weekPlan.secondary_resource, courses, takenUrls),
      'secondary',
      weekPlan.secondary_resource,
    )
  }

  // Last resort for the primary slot only: line the week up with the course list
  // by position, so an unmatched title still shows something actionable.
  if (!out.length) {
    const weekIndex = weeklyPlan.findIndex(wp => wp.week === weekPlan.week)
    if (weekIndex >= 0 && weekIndex < courses.length) {
      push(courses[weekIndex], 'primary', weekPlan.primary_resource)
    }
  }

  return out
}

/** Resource titles the week names but which we could not resolve to a course card. */
export function unresolvedResources(weekPlan: WeekPlan, matched: WeekCourse[]): string[] {
  const matchedTitles = new Set(matched.map(m => m.resourceTitle))
  return [weekPlan.primary_resource, weekPlan.secondary_resource]
    .filter((r): r is string => !!r && !!r.trim())
    .filter(r => !matchedTitles.has(r))
}
