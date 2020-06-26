import json
import os
from dataclasses import dataclass
from typing import List, Union, Dict, Tuple

denied = ('@', '?', '!', '*')


@dataclass
class Abstract:
    __slots__ = ['id', 'text']

    id: str
    text: str

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError('"id" must be string (Abstract)')
        if not isinstance(self.text, str):
            raise TypeError('"text" must be string (Abstract)')


@dataclass
class SimpleQuiz:
    __slots__ = ['id', 'question', 'answer']

    id: str
    question: str
    answer: str

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError('"id" must be string (SimpleQuiz)')
        if not isinstance(self.question, str):
            raise TypeError('"question" must be string (SimpleQuiz)')
        if not isinstance(self.answer, str):
            raise TypeError('"answer" must be string (SimpleQuiz)')


@dataclass
class ChoiceQuiz:
    __slots__ = ['id', 'question', 'choices', 'answer']

    id: str
    question: str
    choices: List[str]
    answer: int

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError('"id" must be string (ChoiceQuiz)')
        if not isinstance(self.question, str):
            raise TypeError('"question" must be string (ChoiceQuiz)')
        if isinstance(self.choices, list):
            for i in self.choices:
                if not isinstance(i, str):
                    raise ValueError('All items of "choices" must be string (ChoiceQuiz)')
        else:
            raise TypeError('"choices" must be list of strings (ChoiceQuiz)')
        if not isinstance(self.answer, int):
            raise TypeError('"answer" must be integer (ChoiceQuiz)')


@dataclass
class MultiChoiceQuiz:
    __slots__ = ['id', 'question', 'choices', 'answers']

    id: str
    question: str
    choices: List[str]
    answers: List[int]

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError('"id" must be string (MultiChoiceQuiz)')
        if not isinstance(self.question, str):
            raise TypeError('"question" must be string (MultiChoiceQuiz)')
        if isinstance(self.choices, list):
            for i in self.choices:
                if not isinstance(i, str):
                    raise TypeError('All items of "choices" must be string (MultiChoiceQuiz)')
        else:
            raise TypeError('"choices" must be list of strings (MultiChoiceQuiz)')
        if isinstance(self.answers, list):
            for i in self.answers:
                if isinstance(i, int):
                    try:
                        self.choices[i]
                    except IndexError:
                        raise IndexError(f'Wrong choice id "{i}" in answers (MultiChoiceQuiz)')
                else:
                    raise TypeError('All items of "answers" must be string (MultiChoiceQuiz)')
        else:
            raise TypeError('"answers" must be list of strings (MultiChoiceQuiz)')


@dataclass
class EditQuiz:
    __slots__ = ['id', 'question', 'task', 'answers']

    id: str
    question: str
    task: str
    answers: List[str]

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError('"id" must be string (EditQuiz)')
        if not isinstance(self.question, str):
            raise TypeError('"question" must be string (EditQuiz)')
        if not isinstance(self.task, str):
            raise TypeError('"task" must be string (EditQuiz)')
        if isinstance(self.answers, list):
            for i in self.answers:
                if not isinstance(i, str):
                    raise TypeError('All items of "answers" must be string (EditQuiz)')
        else:
            raise TypeError('"answers" must be list of strings (EditQuiz)')


class Lesson:
    id: str
    name: str
    parts: List[str]

    def __init__(self, id_: str, name: str, parts: List[str], course):
        self.id = id_

        if isinstance(name, str):
            self.name = name
        else:
            raise TypeError(f'"name" must be string ("{self.id}" lesson)')

        if isinstance(parts, list):
            self.parts = []

            if not len(parts):
                raise ValueError(f'Lesson must have at least one part ("{self.id}" lesson)')

            for i in parts:
                if isinstance(i, str):
                    if i.startswith('@'):
                        if i[1:] in course.abstracts:
                            self.parts.append(i)
                        else:
                            raise IndexError(f'Abstract with id "{i[1:]}" not found ("{self.id}" lesson)')
                    elif i.startswith('?'):
                        if i[1:] in course.quizzes:
                            self.parts.append(i)
                        else:
                            raise IndexError(f'Quiz with id "{i[1:]}" not found ("{self.id}" lesson)')
                else:
                    raise TypeError('All items of "parts" must be strings (Lesson)')
        else:
            raise TypeError('"parts" must be list (Lesson)')

    def resolve(
            self,
            course,
            id_: int
    ) -> Tuple[int, Union[Abstract, SimpleQuiz, ChoiceQuiz, MultiChoiceQuiz, EditQuiz]]:
        id_ = self.parts[id_]

        if id_.startswith('@'):
            return 0, course.abstracts[id_[1:]]
        elif id_.startswith('?'):
            if isinstance((q := course.quizzes[id_[1:]]), SimpleQuiz):
                return 1, q
            elif isinstance(q, ChoiceQuiz):
                return 2, q
            elif isinstance(q, MultiChoiceQuiz):
                return 3, q
            elif isinstance(q, EditQuiz):
                return 4, q


class Section:
    id: str
    name: str
    icon: str
    lessons: List[str]

    def __init__(self, id_: str, name: str, icon: str, lessons: List[str], course):
        self.id = id_

        if isinstance(id_, str):
            if '!' in name:
                raise SyntaxError('You cannot use "!" in section id')
            else:
                self.name = name
        else:
            raise TypeError(f'"name" must be string ("{self.id}" section)')

        if isinstance(name, str):
            if '!' in name:
                raise SyntaxError('You cannot use "!" in section id')
            else:
                self.name = name
        else:
            raise TypeError(f'"name" must be string ("{self.id}" section)')

        if isinstance(icon, str):
            self.icon = icon
        else:
            raise TypeError(f'"icon" must be string ("{self.id}" section)')

        if isinstance(lessons, list):
            self.lessons = []

            if not len(lessons):
                raise ValueError(f'Section must have at least one lesson ("{self.id}" section)')

            for i in lessons:
                if isinstance(i, str):
                    try:
                        self.lessons.append(course.lessons[i].id)
                    except KeyError:
                        raise IndexError(f'Lesson with id "{i}" not found ("{self.id}" section)')
                else:
                    raise TypeError('All items of "lessons" must be strings')
        else:
            raise TypeError('"lessons" must be list')


class Group:
    id: str
    shortcut: List[Union[ChoiceQuiz, MultiChoiceQuiz, SimpleQuiz]]
    sections: List[Section]

    def __init__(self, id_: str, shortcut: List[str], sections: List[str], course):
        self.id = id_

        if isinstance(shortcut, list):
            self.shortcut = []

            for i in shortcut:
                if isinstance(i, str):
                    try:
                        self.shortcut.append(course.quizzes[i])
                    except KeyError:
                        raise IndexError(f'Quiz with id "{i}" not found ("{self.id}" group)')
                else:
                    raise TypeError('All items of "shortcut" must be strings')
        else:
            raise TypeError('"shortcut" must be list')

        if isinstance(sections, list):
            self.sections = []

            for i in sections:
                if isinstance(i, str):
                    try:
                        self.sections.append(course.sections[i])
                    except KeyError:
                        raise IndexError(f'Section with id "{i}" not found ("{self.id}" group)')
                else:
                    raise TypeError('All items of "sections" must be strings')
        else:
            raise TypeError('"sections" must be list')


class Course:
    id: str
    name: str
    title: str
    description: str
    icon: str
    abstracts: Dict[str, Abstract]
    quizzes: Dict[str, Union[ChoiceQuiz, MultiChoiceQuiz, SimpleQuiz]]
    lessons: Dict[str, Lesson]
    sections: Dict[str, Section]
    groups: Dict[str, Group]
    path: str

    def __init__(self, source: str, path: str):
        source = json.loads(source)
        self.path = path

        if 'id' in source:
            if isinstance(source['id'], str):
                self.id = source['id']
            else:
                raise TypeError(f'"id" field must be string in "{path}"')
        else:
            raise IndexError(f'"id" field must be specified in "{path}"')

        if 'name' in source:
            if isinstance(source['name'], str):
                if '@' in source['name']:
                    raise ValueError('"@" cannot be used in course name')
                else:
                    self.name = source['name']
            else:
                raise TypeError(f'"name" field must be string ("{self.id}" course)')
        else:
            raise IndexError(f'"name" field must be specified ("{self.id}" course)')

        if 'title' in source:
            if isinstance(source['title'], str):
                self.title = source['title']
            else:
                raise TypeError(f'"title" field must be string ("{self.id}" course)')
        else:
            raise IndexError(f'"title" field must be specified ("{self.id}" course)')

        if 'description' in source:
            if isinstance(source['description'], str):
                self.description = source['description']
            else:
                raise TypeError(f'"description" field must be string ("{self.id}" course)')
        else:
            raise IndexError(f'"description" must be specified ("{self.id}" course)')

        if 'icon' in source:
            if isinstance(source['icon'], str):
                if os.path.isfile(f'{self.path}/{source["icon"]}'):
                    self.icon = source["icon"]
                else:
                    raise OSError(f'Icon file "{self.path}/{source["icon"]}" not found')
            else:
                raise TypeError(f'"icon" must be string ("{self.id}" course)')
        else:
            raise IndexError(f'"icon" must be specified ("{self.id}" course)')

        if 'abstracts' in source:
            if isinstance(source['abstracts'], dict):
                self.abstracts = {}

                for k, v in source['abstracts'].items():
                    self.abstracts[k] = Abstract(k, v)
            else:
                raise TypeError(f'"abstract" field must be dict in "{self.name}" course')
        else:
            raise IndexError(f'"abstract" field must be specified in "{self.name}" course')

        if 'quizzes' in source:
            if isinstance(source['quizzes'], dict):
                self.quizzes = {}

                for k, v in source['quizzes'].items():
                    if 'type' in v:
                        if isinstance(v['type'], int):
                            self.quizzes[k] = self.quiz_factory(k, **v)
                        else:
                            raise TypeError(f'"type" field must be integer ("{k}" quiz)')
                    else:
                        raise IndexError(f'"type" field not specified ("{k}" quiz)')
            else:
                raise TypeError(f'"quizzes" field must be dict ("{self.name}" course)')
        else:
            raise IndexError(f'"quizzes" field must be specified ("{self.name}" course)')

        if 'lessons' in source:
            if isinstance(source['lessons'], dict):
                self.lessons = {}

                for k, v in source['lessons'].items():
                    if isinstance(v, dict):
                        self.lessons[k] = Lesson(k, course=self, **v)
                    else:
                        raise TypeError(f'Lesson "{k}" must be dict ("{self.name}" course)')
            else:
                raise TypeError(f'"lessons" must be dict ("{self.name}" course)')
        else:
            raise IndexError(f'"lessons" field must be specified ("{self.name}" course)')

        if 'sections' in source:
            if isinstance(source['sections'], dict):
                self.sections = {}

                for k, v in source['sections'].items():
                    self.sections[k] = Section(k, course=self, **v)
            else:
                raise TypeError(f'"sections" must be dict ("{self.name}" course)')
        else:
            raise TypeError(f'"sections" field must be specified ("{self.name}" course)')

        if 'groups' in source:
            if isinstance(source['groups'], dict):
                self.groups = {}

                if not len(source['groups']):
                    raise ValueError(f'Course must have at least one group ("{self.id}" course)')

                for k, v in source['groups'].items():
                    self.groups[k] = Group(k, course=self, **v)
            else:
                raise TypeError(f'"sections" must be dict ("{self.name}" course)')
        else:
            raise TypeError(f'"sections" field must be specified ("{self.name}" course)')

    @staticmethod
    def quiz_factory(id_: str, type: int, **kwargs) -> Union[ChoiceQuiz, MultiChoiceQuiz, SimpleQuiz, EditQuiz]:
        for i in denied:
            if i in id_:
                raise ValueError(f'Quiz id ("{id}") cannot contain those symbols {denied}')

        if type == 0:
            if 'question' not in kwargs:
                raise IndexError(f'"question" field must be specified in quiz with type "{type}"')
            elif 'answer' not in kwargs:
                raise IndexError(f'"answer" field must be specified in quiz with type "{type}"')

            return SimpleQuiz(id_, **kwargs)
        elif type == 1:
            if 'question' not in kwargs:
                raise IndexError(f'"question" field must be specified in quiz with type "{type}"')
            elif 'choices' not in kwargs:
                raise IndexError(f'"choices" field must be specified in quiz with type "{type}"')
            elif 'answer' not in kwargs:
                raise IndexError(f'"answer" field must be specified in quiz with type "{type}"')

            return ChoiceQuiz(id_, **kwargs)
        elif type == 2:
            if 'question' not in kwargs:
                raise IndexError(f'"question" field must be specified in quiz with type "{type}"')
            elif 'choices' not in kwargs:
                raise IndexError(f'"choices" field must be specified in quiz with type "{type}"')
            elif 'answers' not in kwargs:
                raise IndexError(f'"answers" field must be specified in quiz with type "{type}"')

            return MultiChoiceQuiz(id_, **kwargs)
        elif type == 3:
            if 'question' not in kwargs:
                raise IndexError(f'"question" field must be specified in quiz with type "{type}"')
            elif 'task' not in kwargs:
                raise IndexError(f'"task" field must be specified in quiz with type "{type}"')
            elif 'answers' not in kwargs:
                raise IndexError(f'"answers" field must be specified in quiz with type "{type}"')

            return EditQuiz(id_, **kwargs)


class Content:
    path: str = 'content/'
    courses: Dict[str, Course]

    def __init__(self):
        if not os.path.isdir('content/'):
            os.makedirs('content/')
        self.courses = {}

        for i in next(os.walk('content/'))[1]:
            try:
                course = Course(open(f'content/{i}/course.json').read(), f'content/{i}')
                self.courses[course.id] = course
            except FileNotFoundError:
                continue


class Profile:
    courses: Dict[str, Dict[str, int]]

    def __init__(self):
        if not os.path.isdir('content/'):
            os.makedirs('content/')

        if os.path.isfile('content/profile.json') and (profile := open('content/profile.json').read()) and \
                isinstance(profile := json.loads(profile), dict):
            if 'courses' in profile:
                if isinstance(profile['courses'], dict):
                    for k, v in profile['courses'].items():
                        if not isinstance(k, str):
                            raise TypeError('All keys of "courses" must be string (profile)')

                        if isinstance(v, dict):
                            for j, z in v.items():
                                if not isinstance(j, str):
                                    raise TypeError(f'All keys of "{k}" course must be str')
                                elif not isinstance(z, int):
                                    raise TypeError(f'All items of "{k}" course must be int')
                        else:
                            raise TypeError('All items of "courses" must be dict (profile)')
                    else:
                        self.courses = profile['courses']
                else:
                    raise TypeError('"courses" field must be dict (profile)')
            else:
                self.courses = {}
        else:
            self.courses = {}

    def check_lesson(self, content: Content, course: str, section: str, lesson: str) -> int:
        if course not in self.courses:
            self.courses[course] = {}

        if lesson in self.courses[course]:
            if (le := self.courses[course][lesson]) == 0:
                return 0
            elif le > (p := len(content.courses[course].lessons[lesson].parts)):
                return 2
            elif le <= p:
                return 1
        else:
            if i := (lk := content.courses[course].sections[section].lessons).index(lesson):
                if self.check_lesson(content, course, section, lk[i - 1]) == 2:
                    self.courses[course][lesson] = 1
                    return 1
                else:
                    return 0
            else:
                if j := (sk := list(content.courses[course].sections.keys())).index(section):
                    if self.check_section(content, course, sk[j - 1]) == 2:
                        self.courses[course][lesson] = 1
                        return 1
                    else:
                        return 0
                else:
                    self.courses[course][lesson] = 1
                    return 1

    def check_section(self, content: Content, course: str, section: str) -> int:
        if course not in self.courses:
            self.courses[course] = {}

        ss = content.courses[course].sections
        for i in ss[section].lessons:
            if (lc := self.check_lesson(content, course, section, i)) == 0:
                break
            elif lc == 1:
                return 1
        else:
            return 2

        if i := (sk := list(ss.keys())).index(section):
            if self.check_section(content, course, sk[i - 1]) == 2:
                return 1
            else:
                return 0
        else:
            return 1

    def get_lesson_part(self, course: str, lesson: str) -> int:
        if course in self.courses:
            if lesson not in self.courses[course]:
                self.courses[course][lesson] = 0
            return self.courses[course][lesson]
        else:
            return 0

    def dump(self) -> None:
        if not os.path.isdir('content/'):
            os.makedirs('content/')
        json.dump({'courses': self.courses}, open('content/profile.json', 'w+'), indent=2)
