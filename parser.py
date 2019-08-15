import re
from clang.cindex import CursorKind


class Parser:
    """Parser of declarations. Just set of methods
    """

    @staticmethod
    def parse_struct(struct, is_nested=False):
        """Parses a structure

        Args:
            struct (clang.cindex.Cursor): a parsed structure
            is_nested (bool): is structure nested (maybe anonymous)

        Returns:
             (tuple): name and source code of structure
        """
        is_anon = ("(anonymous " in struct.type.spelling) or (struct.spelling == "")
        if is_anon and not is_nested:
            return None

        struct_name = struct.spelling
        struct_src = ["struct %s" % struct_name, "{"]

        for field in struct.get_children():
            field_pair = Parser._parse_field(field)
            if not field_pair:
                continue
            field_name, field_src = field_pair
            struct_src.append(field_src)

        if is_anon:
            struct_src.append("}")
        else:
            struct_src.append("};")

        struct_src = '\n'.join(struct_src)
        return struct_name, struct_src

    @staticmethod
    def parse_union(union, is_nested=False):
        """Parses a union

        Args:
            union (clang.cindex.Cursor): a parsed union
            is_nested (bool): is structure nested (maybe anonymous)

        Returns:
             (tuple): name and source code of union
        """
        is_anon = ("(anonymous " in union.type.spelling) or (union.spelling == "")
        if is_anon and not is_nested:
            return None

        union_name = union.spelling
        union_src = ["union %s" % union_name, "{"]

        for field in union.get_children():
            field_pair = Parser._parse_field(field)
            if not field_pair:
                continue
            field_name, field_src = field_pair
            union_src.append(field_src)

        if is_anon:
            union_src.append("}")
        else:
            union_src.append("};")

        union_src = '\n'.join(union_src)
        return union_name, union_src

    @staticmethod
    def parse_enum(enum):
        """Parses an enumeration

        Args:
            enum (clang.cindex.Cursor): a parsed enumeration

        Returns:
             (tuple): name and source code of an enumeration
        """
        enum_name = enum.spelling

        ret = ["enum " + enum_name + " {"]

        for enum_constant in enum.get_children():
            label = enum_constant.spelling
            children = list(enum_constant.get_children())
            if not children:
                ret.append("%s," % label)
                continue

            value_cursor = children[0]
            value = Parser._get_enum_constant_value(value_cursor)
            ret.append("%s = %s," % (label, value))

        ret.append("};")
        enum_src = '\n'.join(ret)
        return enum_name, enum_src

    @staticmethod
    def parse_typedef(typedef):
        """Parses a typedef statement

        Args:
            typedef (clang.cindex.Cursor): a parsed typedef statement

        Returns:
             (tuple): name and source code of a typedef
        """
        typedef_name = typedef.spelling
        underlying_typename = typedef.underlying_typedef_type.spelling

        if '(anonymous struct' in underlying_typename or underlying_typename.startswith('struct'):
            child = list(typedef.get_children())[0]
            if child.kind == CursorKind.STRUCT_DECL and child.spelling == '':
                struct = child
                struct_name, struct_src = Parser.parse_struct(struct, is_nested=True)
                typedef_src = "typedef %s %s;" % (struct_src, typedef.spelling)
            elif child.kind == CursorKind.TYPE_REF:
                typedef_src = "typedef %s %s;" % (underlying_typename, typedef.spelling)
            else:
                return None
        elif '(anonymous union' in underlying_typename or underlying_typename.startswith('union'):
            child = list(typedef.get_children())[0]
            if child.kind == CursorKind.UNION_DECL and child.spelling == '':
                union = child
                union_name, union_src = Parser.parse_union(union, is_nested=True)
                typedef_src = "typedef %s %s;" % (union_src, typedef.spelling)
            elif child.kind == CursorKind.TYPE_REF:
                typedef_src = "typedef %s %s;" % (underlying_typename, typedef.spelling)
            else:
                return None
        else:
            # For case "typedef int (*bar)(int *, void*);"
            if re.findall(r'\(\*+\)', underlying_typename):
                pos = underlying_typename.find(')(')
                src = ("typedef " + underlying_typename[:pos] + " %s " + underlying_typename[pos:] + ";") % typedef_name
                return typedef_name, src

            # For case "typedef int foo(int *, void *);"
            pos = underlying_typename.find('(')
            if pos > -1:
                src = ("typedef " + underlying_typename[:pos - 1] + " %s " + underlying_typename[
                                                                             pos:] + ";") % typedef_name
                return typedef_name, src

            typedef_src = "typedef %s %s;" % (underlying_typename, typedef.spelling)

        return typedef_name, typedef_src

    @staticmethod
    def _parse_field(field):
        """Parses a field

        Args:
            field (clang.cindex.Cursor): field of structure or union

        Returns:
            (tuple): name and source code of a field
        """
        field_name = field.spelling
        type_name = field.type.spelling

        if Parser._is_primitive_field(field):

            if field.kind == CursorKind.PACKED_ATTR:
                return None

            if field.is_bitfield():
                bit_length = list(list(field.get_children())[0].get_tokens())[0].spelling
                field_src = "%s %s: %s;" % (type_name, field_name, bit_length)
                return field_name, field_src

            elif Parser._is_array(field):
                pos = type_name.find('[')
                field_src = type_name[:pos] + field_name + type_name[pos:] + ";"
                return field_name, field_src

            elif re.findall(r'\(\*+\)', type_name):
                pos = type_name.find(')(')
                field_src = (type_name[:pos] + " %s " + type_name[pos:] + ";") % field_name
                return field_name, field_src

            else:
                field_src = "%s %s;" % (type_name, field_name)
                return field_name, field_src

        elif Parser._is_struct(field):
            if field.kind == CursorKind.FIELD_DECL:
                struct = list(field.get_children())[0]
                struct_name, struct_src = Parser.parse_struct(struct, is_nested=True)
            else:
                struct = Parser.parse_struct(field, is_nested=False)
                if not struct:
                    return None
                struct_name, struct_src = struct

            if Parser._is_array(field):
                pos = type_name.find('[')
                struct_src = "%s %s%s;" % (struct_src, field.spelling, type_name[pos:])
            else:
                struct_src = "%s %s;" % (struct_src, field.spelling)
            return field.spelling, struct_src
        elif Parser._is_union(field):
            if field.kind == CursorKind.FIELD_DECL:
                union = list(field.get_children())[0]
                union_name, union_src = Parser.parse_union(union, is_nested=True)
            else:
                union = Parser.parse_union(field, is_nested=True)
                if not union:
                    return None
                union_name, union_src = union

            if Parser._is_array(field):
                pos = type_name.find('[')
                union_src = "%s %s%s;" % (union_src, field.spelling, type_name[pos:])
            else:
                union_src = "%s %s;" % (union_src, field.spelling)
            return field.spelling, union_src
        else:
            return None

    @staticmethod
    def _is_struct(field):
        """Check if a structure

        Args:
            field (clang.cindex.Cursor): field of structure or union

        Returns:
            (bool): is field a structure
        """
        if field.kind == CursorKind.STRUCT_DECL:
            return True

        children = list(field.get_children())
        if children:
            if children[0].kind == CursorKind.STRUCT_DECL:
                return True

        return False

    @staticmethod
    def _is_union(field):
        """Check if a union

        Args:
            field (clang.cindex.Cursor): field of structure or union

        Returns:
            (bool): is field a union
        """
        if field.kind == CursorKind.UNION_DECL:
            return True

        children = list(field.get_children())
        if children:
            if children[0].kind == CursorKind.UNION_DECL:
                return True

        return False

    @staticmethod
    def _is_primitive_field(field):
        """Check if a primitive field (not a structure or union)

        Args:
            field (clang.cindex.Cursor): field of structure or union

        Returns:
            (bool): is field a primitive
        """
        # For such cases as PACKED_ATTR, UNEXPOSED_ATTR and etc
        if not field.kind == CursorKind.FIELD_DECL:
            return False

        children = list(field.get_children())
        if children:
            kinds = set(map(lambda x: x.kind, children))
            if kinds & {CursorKind.STRUCT_DECL, CursorKind.UNION_DECL}:
                return False

        return True

    @staticmethod
    def _is_array(field):
        """Check if a field is an array

        Args:
            field (clang.cindex.Cursor): field of structure or union

        Returns:
            (bool): is field an array
        """
        type_name = field.type.spelling
        if re.findall(r'\[[A-Za-z0-9]*\]', type_name):
            return True
        else:
            return False

    @staticmethod
    def _get_enum_constant_value(element):
        """Gets value of an enumeration constant

        Args:
            element (clang.cindex.Cursor): an enumeration constant

        Returns:
            (str): value of an enumeration constant
        """
        tokens = map(lambda x: x.spelling, list(element.get_tokens()))
        return ' '.join(tokens)
