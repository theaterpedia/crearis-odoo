/*
 * ---------------------
 * CONFIGURATION OPTIONS
 * ---------------------
 * input: project, show, versions
 * 
 * project: The name of the project to filter tasks by. Default is 'devproject'.
 * show: An array of strings to determine which task groups to show.
 *        Options are 'controlling', 'priority', 'normal', and 'someday'.
 * versions: An array of version tags to filter tasks by. Default is ['#v1', '#v2', '#v3'].
 * showDetails: A boolean to determine whether to show task details. Default is false.
 * 
 * Add the folders, tags, and headings which should be excluded.
 * Tasks found on pages with these tags or paths will not appear in the Tasks page.
 * Headings will to exclude tasks that fall under a heading with this name.
 */
const config = {
  tags: {
    project: '#' + (input.project || 'devproject'),
    tracked: '#tracked',
    controlling: '#controlling',
    priority: '#🔼'
  },
  showControlling: (input.show && input.show.includes('controlling')) || !input.show,
  showPriority: (input.show && input.show.includes('priority')) || !input.show,
  showNormal: (input.show && input.show.includes('normal')) || !input.show,
  showSomeday: (input.show && input.show.includes('someday')) || false,
  showDetails: input.showDetails || false,
  maxVersion: 10,
  icons: {
    untracked: '🔶',
    priority: '🔼',
    controlling: '⏳'
  }
}

const globalExclude = {
  folders: [
    'Utility',
    'dev/x_images',
    'dev/X_Assets',
    'dev/Z_Utility',
    'dev/_meta',
    'x_images',
    'Z_Utility',
    '03_PROJECTS/Projects/GTMD/x_text',
  ],
  tags: [
    '#exclude-master-tasklist',
    '#completed'
  ],
  headings: [
    '🌱 Daily Habits',
    'Planungsstatus',
  ],

}
/*
 * When displaying tasks from a project, tasks that fall under headings with these
 * names won't have these headings displayed when showing the project info
 */
const hideSubsectionName = [
  'Todo',
  'Tasks'
]

/*
 * ----------------------------
 * END OF CONFIGURATION OPTIONS
 * ----------------------------
 */

// Set up the variables to store the tasks and projects
const tasks = []
const noNextAction = []
const excludeItems = ['', ...globalExclude.tags]
globalExclude.folders.forEach(folder => excludeItems.push(`"${folder}"`))
const globalExcludeString = excludeItems.join(' AND -')

const VersionTags = input.versions
// Define groups for master tasklist page
const Groups = {
  Waiting: 0,
  Priority: 1,
  Normal: 2,
  Someday: 3
}

/**
 * Take a task and the page it's from, and return a formatted element for the tasks array
 * @param {*} task 
 * @param {*} page 
 * @returns {object}
 */
function generateTaskElement(task, page) {
  let group = Groups.Normal
  if (task.tags.includes('#x_backlog')) {
    group = Groups.Someday
  } else if (task.tags.includes('#controlling')) {
    group = Groups.Waiting
  } else if (task.text.includes('🔼') || page.tags.includes('#🔼')) {
    group = Groups.Priority
  }
  return {
    task: task,
    date: (page.created ? page.created.ts || moment(page.created).valueOf() : null) || page.ctime.ts,
    group: group,
    version: task.version,
    title: task.text
  }
}

function getWeekStartString(weekNumber) {
  // Calculate the start date of the week based on the week number
  const date = new Date("2025-12-30") // + (weekNumber - 1) * 7
  date.setDate(date.getDate() + (weekNumber - 1) * 7)
  return date.getDate() + "." + (date.getMonth() + 1) // result.getDay() + "." + result.getMonth()
}

function getWeekDayString(weekNumber, dayNumber) {
  // Calculate the start date of the week based on the week number
  const date = new Date("2025-12-30") // + (weekNumber - 1) * 7 + (dayNumber - 1)
  date.setDate(date.getDate() + (weekNumber - 1) * 7 + (dayNumber - 2))
  return date.getDate() + "." + (date.getMonth() + 1)
}

/*
 * Process projects
 */
dv.pages(config.tags.project + globalExcludeString).file
  .forEach(project => {
    const sections = []
    if (!project.tasks.filter(t => !t.completed && t.text).length) {
      // There is no next action for this project
      noNextAction.push(project)
    } else {
      project.tasks
        .where(t => !t.completed && t.text)
        .forEach(task => {
          const sectionName = task.section.subpath || 'root'
          // HANS: changes made here delete sectionName-Logic
          // Select only the first task from each section. This allows task sequencing.
          // if ((!sections.includes(sectionName) && !sectionName.includes('exclude')) || sectionName.includes('🟰')) {
          // sections.push(sectionName)
          if ((!sectionName.includes('exclude') || sectionName.includes('🟰')) && VersionTags.includes(task.tags ? task.tags[0] : '#xxx')) {
            if (!sections.includes(sectionName)) sections.push(sectionName)
            let subSection = ''
            let headingLine = 1
            task.version = task.tags[0]
            if (
              // There is a subpath/heading
              task.section.subpath &&
              // And it's not one of our whitelisted headings which don't require a notated sub-section
              !hideSubsectionName.includes(sectionName) &&
              // And it doesn't match the project name
              sectionName !== project.name.replace(/\W/g, ' ')
            ) {
              // Add it as a sub-section to the project name
              subSection = ` > ${sectionName}`
              // Find the line-position of the heading for this task
              const file = app.fileManager.vault.getAbstractFileByPath(project.path)
              const headings = app.metadataCache.getFileCache(file).headings
              const match = headings.find(x => x.heading === sectionName)
              headingLine = match ? match.position.start.line : task.line - 1
            }
            task.fileLink = dv.fileLink(project.path, { text: project.name })
            const isWeek = task.text.startsWith('#kw')
            const weekNumber = isWeek ? task.text.substring(3, 5) : 0
            task.text = task.text.substring(6) + ` 🗃️ *${project.name}${subSection}*`
            if (isWeek && task.text.substring(0, 1).match(/^[1-7]$/)) {
              // if task.text starts with digit 1-7 followed by a space, then we replace it with the day-name
              const dayNumber = task.text.substring(0, 1)
              const dayName = ['  MO', ' DI', ' MI', 'DO', 'FR', 'SA', 'SO'][dayNumber - 1]

              task.text = `🗓️ **${dayName}, ${getWeekDayString(weekNumber, dayNumber)}**` + task.text.substring(1)
            }
            task.subversion = task.text.substring(6, 7) + ` 🗃️ *${project.name}${subSection}*`
            tasks.push(generateTaskElement(task, project))
          }
        })
    }
  })

/*
 * Dev-Project tasks
 
  dv.pages('#devproject' + globalExcludeString)
    .where(p => p.file.tasks.length && !p['kanban-plugin'] && !p['exclude_master_tasklist']).file
    .forEach(page => {
      page.tasks
        .where(t =>
          t.text && // where the task has text (is not blank)
          !t.completed && // and not completed
          !t.tags.includes('#exclude') && // and not excluded
          (!t.header.subpath || !t.header.subpath.includes('exclude')) &&
          !globalExclude.headings.includes(t.header.subpath) && // and the heading is not excluded by text
          !t.header.subpath.includes(config.icons.untracked) // and the heading is not excluded by icon
        )
        .forEach(task => tasks.push(generateTaskElement(task, page)))
    })
*/

// Sort tasks into groups, then ascending by created time
tasks.sort((a, b) => a.group - b.group)

/**
 * Output a formatted task list
 * @param {number|null} group - Filter for tasks in a particular group, or null for all tasks
 * @param {string|null} header - The text header for the task list
 */
function taskList(group, header) {
  const list = isNaN(group) ? tasks : tasks.filter(x => x.group === group)
  if (list.length) {
    if (header) dv.header(2, header)
    for (const tVersion of VersionTags) {
      const vList = isNaN(list) ? list.filter(y => y.version === tVersion) : list
      if (vList.length) {
        const vTasks = vList.sort((a, b) => ('' + a.title).localeCompare(b.title))
        const tagType = tVersion.substring(0, 2) === '#v' ? 'sprint' : tVersion.substring(0, 3) === '#kw' ? 'woche' : 'tag'
        const tagName = tagType === 'sprint' ? tVersion.substring(2, 3) + '.' + tVersion.substring(3) : tagType === 'woche' ? tVersion.substring(1, 5) : tVersion
        if (config.showDetails) {
          dv.header(3, tagType.toUpperCase() + ": " + tagName)
          dv.taskList(vTasks.map(x => x.task), false)
        } else {
          dv.table([tagType.toUpperCase() + ": " + tagName, 'Page'], vTasks.map(x => [
            x.task.text,
            dv.fileLink(x.task.fileLink.path),
          ]))
        }
        // 
      }
    }
  }
}


/* Projects without next action
if (noNextAction.length) {
  dv.header(2, '🚩 Projects without next actions')
  dv.list(noNextAction.map(p => p.link))
} */

// Output the task list

if (config.showControlling) taskList(Groups.Waiting, config.icons.controlling + ' ich warte/Controlling')
if (config.showPriority) taskList(Groups.Priority, config.icons.priority + ' Priorität')
if (config.showNormal) taskList(Groups.Normal, '✅ Agenda')
if (config.showSomeday) taskList(Groups.Someday, '💤 Someday')
