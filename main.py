import random
import sys
import threading

from PySide2 import QtWidgets, QtWebEngineWidgets, QtCore, QtGui
from flask import Flask, render_template, send_from_directory, abort, redirect, request

import library


def shuffle(a: list) -> list:  # Shuffle list
    b = a.copy()
    random.shuffle(b)
    return b


def prepare(text: str, replace: list) -> str:  # Format EditQuiz task
    to_replace = []
    for i, v in enumerate(replace):
        to_replace.append(
            f'<div class="edit-answer"><span>{v}</span><input type="text" name="a-{i}" maxlength="{len(v)}"></div>')

    return text.format(*to_replace).replace('{{', '{').replace('}}', '}')


def setup_server(profile: library.Profile, content: library.Content):  # Prepare web server
    server = Flask(__name__, static_folder='gui/assets', template_folder='gui')

    @server.route('/')
    def home():  # Home page (with all courses)
        return render_template('main.html', **{'courses': content.courses})

    @server.route('/favicon.ico')
    def favicon():
        return send_from_directory('gui/assets', 'icon.svg')

    @server.route('/<course>')
    def _course(course):  # Course page (with all course sections)
        if course in content.courses:  # Validate course
            return render_template(
                'course.html',
                **{
                    'course': content.courses[course].name,
                    'groups': {k: {
                        i.id: {
                            'name': i.name,
                            'icon': i.icon,
                            'status': profile.check_section(content, course, i.id)
                        } for i in v.sections
                    } for k, v in content.courses[course].groups.items()}
                }
            )
        else:
            abort(404, f'Course "{course}" not found')

    @server.route('/<course>/')
    def _course_redirect(course):  # Redirect from wrong url
        return redirect(f'/{course}')

    @server.route('/<course>/<section>')
    def _section(course, section):  # Section page (with all section lessons)
        if course in content.courses:  # Validate course
            if section in content.courses[course].sections:  # Validate section
                if profile.check_section(content, course, section) != 0:  # Check access
                    return render_template(
                        'section.html',
                        **{
                            'course': course,
                            'lessons': {i: {
                                'status': profile.check_lesson(content, course, section, i),
                                'name': content.courses[course].lessons[i].name
                            } for i in content.courses[course].sections[section].lessons
                            },
                            'section': content.courses[course].sections[section].name
                        }
                    )
                else:
                    abort(403, f'Section doesn\'t opened yet')
            else:
                abort(404, f'Section "{section}" not found')
        else:
            abort(404, f'Course "{course}" not found')

    @server.route('/<course>/<section>/')
    def _section_redirect(course, section):  # Redirection from wrong url
        return redirect(f'/{course}/{section}')

    @server.route('/<course>/<section>/<lesson>')
    def _lesson(course, section, lesson):  # Lesson page (redirect to lessons part)
        if course in content.courses:  # Validate course
            if section in content.courses[course].sections:  # Validate section
                if lesson in content.courses[course].sections[section].lessons:  # Validate lesson
                    if profile.check_lesson(content, course, section, lesson):  # Check access
                        return redirect(
                            f'''./{lesson}/{
                            p if (p := profile.get_lesson_part(course, lesson)) <=
                                 (l := len(content.courses[course].lessons[lesson].parts)) else l}''')
                    else:
                        abort(403, f'This lesson doesn\'t opened yet')
                else:
                    abort(404, f'Lesson "{lesson}" not found')
            else:
                abort(404, f'Section "{section}" not found')
        else:
            abort(404, f'Course "{course}" not found')

    @server.route('/<course>/<section>/<lesson>/')
    def _lesson_redirect(course, section, lesson):  # Redirection from wrong url
        return redirect(f'/{course}/{section}/{lesson}')

    @server.route('/<course>/<section>/<lesson>/<int:pos>', methods=['GET', 'POST'])
    def _lesson_pos(course, section, lesson, pos):  # Lesson part page (contains abstract or quiz)
        if course in content.courses:  # Validate course
            if section in content.courses[course].sections:  # Validate section
                if lesson in content.courses[course].sections[section].lessons:  # Validate lesson
                    if pos <= (p := profile.get_lesson_part(course, lesson)) and pos:  # Validate access
                        if request.method == 'GET':  # Return page
                            return render_template(
                                'lesson.html',
                                **{
                                    'alert': True if 'alert' in request.args else False,
                                    'content': content.courses[course].lessons[lesson].resolve(
                                        content.courses[course], pos - 2 if pos > len(
                                            content.courses[course].lessons[lesson].parts) else pos - 1),
                                    'lesson': content.courses[course].lessons[lesson],
                                    'part': p,
                                    'pos': pos,
                                    'section': content.courses[course].sections[section]
                                }
                            )
                        elif request.method == 'POST':  # Check and update progress
                            type_, part = content.courses[course].lessons[lesson].resolve(
                                content.courses[course],
                                pos - 2 if pos > (
                                    lp := len(content.courses[course].lessons[lesson].parts)) else pos - 1)

                            if type_ == 0:  # Abstract progress
                                pass
                            elif type_ == 1:  # Check SimpleQuiz
                                if 'answer' not in request.form or request.form['answer'] != part.answer:
                                    return redirect(f'./{pos}?alert=1')
                            elif type_ == 2:  # Check ChoiceQuiz
                                if 'choice' not in request.form or int(request.form['choice']) != part.answer:
                                    return redirect(f'./{pos}?alert=1')
                            elif type_ == 3:  # Check MultiChoiceQuiz
                                for i, v in enumerate(part.choices):
                                    if i in part.answers and (v not in request.form or request.form[v] != 'on'):
                                        return redirect(f'./{pos}?alert=1')
                                    elif i not in part.answers and (v in request.form):
                                        return redirect(f'./{pos}?alert=1')
                            elif type_ == 4:  # Check EditQuiz
                                for i, v in enumerate(part.answers):
                                    if f'a-{i}' not in request.form or request.form[f'a-{i}'] != v:
                                        return redirect(f'./{pos}?alert=1')
                            else:
                                abort(500, 'Unknown part type')

                            if profile.courses[course][lesson] <= lp:  # Update progress
                                profile.courses[course][lesson] += 1

                            # Redirect to next part
                            if profile.courses[course][lesson] > lp:
                                if pos + 1 > lp:
                                    return redirect(f'../../{section}')
                            return redirect(f'./{pos + 1}')
                    else:
                        if p:
                            return redirect(f'./{p}')
                        else:
                            return redirect(f'../../{section}')
                else:
                    abort(404, f'Lesson "{lesson}" not found')
            else:
                abort(404, f'Section "{section}" not found')
        else:
            abort(404, f'Course "{course}" not found')

    @server.route('/@content/<path:file>')
    def _content(file):  # Get course file
        return send_from_directory('content/', file, as_attachment=True)

    @server.errorhandler(Exception)
    def _error(error):  # Error page
        return render_template('error.html', **{'error': error})

    @server.after_request
    def _after(response):  # Cache control
        response.headers['cache-control'] = 'max-age=10'
        return response

    return server


class App:
    app: QtWidgets.QApplication
    content: library.Content
    gui: QtWebEngineWidgets.QWebEngineView
    profile: library.Profile
    server: Flask
    server_thread: threading.Thread
    window: QtWidgets.QMainWindow

    def __init__(self):
        self.profile = library.Profile()
        self.content = library.Content()

        # Start web server
        self.server = setup_server(self.profile, self.content)
        self.server.jinja_env.globals.update({'len': len, 'enum': enumerate, 'shuffle': shuffle, 'prepare': prepare})
        self.server_thread = threading.Thread(target=self.server.run, args=('localhost', 20052), daemon=True)
        self.server_thread.start()

        # Start app
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = QtWidgets.QMainWindow()

        # Setup app
        self.window.setWindowTitle('Learn App')
        self.window.resize(1280, 720)
        self.window.setMinimumSize(QtCore.QSize(640, 480))

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("gui/assets/icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.window.setWindowIcon(icon)

        self.gui = QtWebEngineWidgets.QWebEngineView()
        self.gui.setUrl(QtCore.QUrl('http://localhost:20052/'))

        # Show app
        self.window.setCentralWidget(self.gui)
        self.window.show()

        self.app.exec_()

        self.profile.dump()


if __name__ == '__main__':
    app = App()
