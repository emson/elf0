└── docs
    └── api
        ├── aliases.md
        ├── annotated_handlers.md
        ├── base_model.md
        ├── config.md
        ├── dataclasses.md
        ├── errors.md
        ├── experimental.md
        ├── fields.md
        ├── functional_serializers.md
        ├── functional_validators.md
        ├── json_schema.md
        ├── networks.md
        ├── pydantic_core.md
        ├── pydantic_core_schema.md
        ├── pydantic_extra_types_color.md
        ├── pydantic_extra_types_coordinate.md
        ├── pydantic_extra_types_country.md
        ├── pydantic_extra_types_currency_code.md
        ├── pydantic_extra_types_isbn.md
        ├── pydantic_extra_types_language_code.md
        ├── pydantic_extra_types_mac_address.md
        ├── pydantic_extra_types_payment.md
        ├── pydantic_extra_types_pendulum_dt.md
        ├── pydantic_extra_types_phone_numbers.md
        ├── pydantic_extra_types_routing_numbers.md
        ├── pydantic_extra_types_script_code.md
        ├── pydantic_extra_types_semantic_version.md
        ├── pydantic_extra_types_timezone_name.md
        ├── pydantic_extra_types_ulid.md
        ├── pydantic_settings.md
        ├── root_model.md
        ├── standard_library_types.md
        ├── type_adapter.md
        ├── types.md
        ├── validate_call.md
        └── version.md


/docs/api/aliases.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.aliases
2 | 


--------------------------------------------------------------------------------
/docs/api/annotated_handlers.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.annotated_handlers
2 | 


--------------------------------------------------------------------------------
/docs/api/base_model.md:
--------------------------------------------------------------------------------
 1 | Pydantic models are simply classes which inherit from `BaseModel` and define fields as annotated attributes.
 2 | 
 3 | ::: pydantic.BaseModel
 4 |     options:
 5 |         show_root_heading: true
 6 |         merge_init_into_class: false
 7 |         group_by_category: false
 8 |         # explicit members list so we can set order and include `__init__` easily
 9 |         members:
10 |           - __init__
11 |           - model_config
12 |           - model_fields
13 |           - model_computed_fields
14 |           - __pydantic_core_schema__
15 |           - model_extra
16 |           - model_fields_set
17 |           - model_construct
18 |           - model_copy
19 |           - model_dump
20 |           - model_dump_json
21 |           - model_json_schema
22 |           - model_parametrized_name
23 |           - model_post_init
24 |           - model_rebuild
25 |           - model_validate
26 |           - model_validate_json
27 |           - model_validate_strings
28 | 
29 | ::: pydantic.create_model
30 |     options:
31 |         show_root_heading: true
32 | 


--------------------------------------------------------------------------------
/docs/api/config.md:
--------------------------------------------------------------------------------
 1 | ::: pydantic.config
 2 |     options:
 3 |       group_by_category: false
 4 |       members:
 5 |         - ConfigDict
 6 |         - with_config
 7 |         - ExtraValues
 8 |         - BaseConfig
 9 | 
10 | ::: pydantic.alias_generators
11 |     options:
12 |       show_root_heading: true
13 | 


--------------------------------------------------------------------------------
/docs/api/dataclasses.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.dataclasses
2 | 


--------------------------------------------------------------------------------
/docs/api/errors.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.errors
2 | 


--------------------------------------------------------------------------------
/docs/api/experimental.md:
--------------------------------------------------------------------------------
 1 | # Experimental API
 2 | 
 3 | ## Pipeline API
 4 | 
 5 | ::: pydantic.experimental.pipeline
 6 |     options:
 7 |         members:
 8 |             - _Pipeline
 9 | 
10 | ## Arguments schema API
11 | 
12 | ::: pydantic.experimental.arguments_schema
13 |     options:
14 |         members:
15 |             - generate_arguments_schema
16 | 


--------------------------------------------------------------------------------
/docs/api/fields.md:
--------------------------------------------------------------------------------
 1 | ::: pydantic.fields
 2 |     options:
 3 |       group_by_category: false
 4 |       members:
 5 |         - Field
 6 |         - FieldInfo
 7 |         - PrivateAttr
 8 |         - ModelPrivateAttr
 9 |         - computed_field
10 |         - ComputedFieldInfo
11 | 


--------------------------------------------------------------------------------
/docs/api/functional_serializers.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.functional_serializers
2 | 


--------------------------------------------------------------------------------
/docs/api/functional_validators.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.functional_validators
2 | 


--------------------------------------------------------------------------------
/docs/api/json_schema.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.json_schema
2 | 


--------------------------------------------------------------------------------
/docs/api/networks.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.networks
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_core.md:
--------------------------------------------------------------------------------
 1 | ::: pydantic_core
 2 |     options:
 3 |         allow_inspection: false
 4 |         show_source: false
 5 |         members:
 6 |         - SchemaValidator
 7 |         - SchemaSerializer
 8 |         - ValidationError
 9 |         - ErrorDetails
10 |         - InitErrorDetails
11 |         - SchemaError
12 |         - PydanticCustomError
13 |         - PydanticKnownError
14 |         - PydanticOmit
15 |         - PydanticUseDefault
16 |         - PydanticSerializationError
17 |         - PydanticSerializationUnexpectedValue
18 |         - Url
19 |         - MultiHostUrl
20 |         - MultiHostHost
21 |         - ArgsKwargs
22 |         - Some
23 |         - TzInfo
24 |         - to_json
25 |         - from_json
26 |         - to_jsonable_python
27 |         - list_all_errors
28 |         - ErrorTypeInfo
29 |         - __version__
30 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_core_schema.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_core.core_schema
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_color.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.color
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_coordinate.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.coordinate
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_country.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.country
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_currency_code.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.currency_code
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_isbn.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.isbn
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_language_code.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.language_code
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_mac_address.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.mac_address
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_payment.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.payment
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_pendulum_dt.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.pendulum_dt
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_phone_numbers.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.phone_numbers
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_routing_numbers.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.routing_number
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_script_code.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.script_code
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_semantic_version.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.semantic_version
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_timezone_name.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.timezone_name
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_extra_types_ulid.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_extra_types.ulid
2 | 


--------------------------------------------------------------------------------
/docs/api/pydantic_settings.md:
--------------------------------------------------------------------------------
1 | ::: pydantic_settings
2 | 


--------------------------------------------------------------------------------
/docs/api/root_model.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.root_model
2 | 


--------------------------------------------------------------------------------
/docs/api/standard_library_types.md:
--------------------------------------------------------------------------------
   1 | ---
   2 | description: Support for common types from the Python standard library.
   3 | ---
   4 | 
   5 | Pydantic supports many common types from the Python standard library. If you need stricter processing see
   6 | [Strict Types](../concepts/types.md#strict-types), including if you need to constrain the values allowed (e.g. to require a positive `int`).
   7 | 
   8 | !!! note
   9 |     Pydantic still supports older (3.8-) typing constructs like `typing.List` and `typing.Dict`, but
  10 |     it's best practice to use the newer types like `list` and `dict`.
  11 | 
  12 | ## Booleans
  13 | 
  14 | A standard `bool` field will raise a `ValidationError` if the value is not one of the following:
  15 | 
  16 | * A valid boolean (i.e. `True` or `False`),
  17 | * The integers `0` or `1`,
  18 | * a `str` which when converted to lower case is one of
  19 |   `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
  20 | * a `bytes` which is valid per the previous rule when decoded to `str`
  21 | 
  22 | !!! note
  23 |     If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can
  24 |     use [`StrictBool`](../api/types.md#pydantic.types.StrictBool).
  25 | 
  26 | Here is a script demonstrating some of these behaviors:
  27 | 
  28 | ```python
  29 | from pydantic import BaseModel, ValidationError
  30 | 
  31 | 
  32 | class BooleanModel(BaseModel):
  33 |     bool_value: bool
  34 | 
  35 | 
  36 | print(BooleanModel(bool_value=False))
  37 | #> bool_value=False
  38 | print(BooleanModel(bool_value='False'))
  39 | #> bool_value=False
  40 | print(BooleanModel(bool_value=1))
  41 | #> bool_value=True
  42 | try:
  43 |     BooleanModel(bool_value=[])
  44 | except ValidationError as e:
  45 |     print(str(e))
  46 |     """
  47 |     1 validation error for BooleanModel
  48 |     bool_value
  49 |       Input should be a valid boolean [type=bool_type, input_value=[], input_type=list]
  50 |     """
  51 | ```
  52 | 
  53 | ## Datetime Types
  54 | 
  55 | Pydantic supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
  56 | types:
  57 | 
  58 | ### [`datetime.datetime`][]
  59 | 
  60 | * `datetime` fields will accept values of type:
  61 |     * `datetime`; an existing `datetime` object
  62 |     * `int` or `float`; assumed as Unix time, i.e. seconds (if >= `-2e10` and <= `2e10`) or milliseconds
  63 |       (if < `-2e10`or > `2e10`) since 1 January 1970
  64 |     * `str`; the following formats are accepted:
  65 |         * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
  66 |         * `YYYY-MM-DD` is accepted in lax mode, but not in strict mode
  67 |         * `int` or `float` as a string (assumed as Unix time)
  68 |     * [`datetime.date`][] instances are accepted in lax mode, but not in strict mode
  69 | 
  70 | ```python
  71 | from datetime import datetime
  72 | 
  73 | from pydantic import BaseModel
  74 | 
  75 | 
  76 | class Event(BaseModel):
  77 |     dt: datetime = None
  78 | 
  79 | 
  80 | event = Event(dt='2032-04-23T10:20:30.400+02:30')
  81 | 
  82 | print(event.model_dump())
  83 | """
  84 | {'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(+02:30))}
  85 | """
  86 | ```
  87 | 
  88 | ### [`datetime.date`][]
  89 | 
  90 | * `date` fields will accept values of type:
  91 |     * `date`; an existing `date` object
  92 |     * `int` or `float`; handled the same as described for `datetime` above
  93 |     * `str`; the following formats are accepted:
  94 |         * `YYYY-MM-DD`
  95 |         * `int` or `float` as a string (assumed as Unix time)
  96 | 
  97 | ```python
  98 | from datetime import date
  99 | 
 100 | from pydantic import BaseModel
 101 | 
 102 | 
 103 | class Birthday(BaseModel):
 104 |     d: date = None
 105 | 
 106 | 
 107 | my_birthday = Birthday(d=1679616000.0)
 108 | 
 109 | print(my_birthday.model_dump())
 110 | #> {'d': datetime.date(2023, 3, 24)}
 111 | ```
 112 | 
 113 | ### [`datetime.time`][]
 114 | 
 115 | * `time` fields will accept values of type:
 116 | 
 117 |     * `time`; an existing `time` object
 118 |     * `str`; the following formats are accepted:
 119 |         * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
 120 | 
 121 | ```python
 122 | from datetime import time
 123 | 
 124 | from pydantic import BaseModel
 125 | 
 126 | 
 127 | class Meeting(BaseModel):
 128 |     t: time = None
 129 | 
 130 | 
 131 | m = Meeting(t=time(4, 8, 16))
 132 | 
 133 | print(m.model_dump())
 134 | #> {'t': datetime.time(4, 8, 16)}
 135 | ```
 136 | 
 137 | ### [`datetime.timedelta`][]
 138 | 
 139 | * `timedelta` fields will accept values of type:
 140 | 
 141 |     * `timedelta`; an existing `timedelta` object
 142 |     * `int` or `float`; assumed to be seconds
 143 |     * `str`; the following formats are accepted:
 144 |         * `[-][[DD]D,]HH:MM:SS[.ffffff]`
 145 |             * Ex: `'1d,01:02:03.000004'` or `'1D01:02:03.000004'` or `'01:02:03'`
 146 |         * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)
 147 | 
 148 | ```python
 149 | from datetime import timedelta
 150 | 
 151 | from pydantic import BaseModel
 152 | 
 153 | 
 154 | class Model(BaseModel):
 155 |     td: timedelta = None
 156 | 
 157 | 
 158 | m = Model(td='P3DT12H30M5S')
 159 | 
 160 | print(m.model_dump())
 161 | #> {'td': datetime.timedelta(days=3, seconds=45005)}
 162 | ```
 163 | 
 164 | ## Number Types
 165 | 
 166 | Pydantic supports the following numeric types from the Python standard library:
 167 | 
 168 | ### [`int`][]
 169 | 
 170 | * Pydantic uses `int(v)` to coerce types to an `int`;
 171 |   see [Data conversion](../concepts/models.md#data-conversion) for details on loss of information during data conversion.
 172 | 
 173 | ### [`float`][]
 174 | 
 175 | * Pydantic uses `float(v)` to coerce values to floats.
 176 | 
 177 | ### [`enum.IntEnum`][]
 178 | 
 179 | * Validation: Pydantic checks that the value is a valid `IntEnum` instance.
 180 | * Validation for subclass of `enum.IntEnum`: checks that the value is a valid member of the integer enum;
 181 |   see [Enums and Choices](#enum) for more details.
 182 | 
 183 | ### [`decimal.Decimal`][]
 184 | 
 185 | * Validation: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`.
 186 | * Serialization: Pydantic serializes [`Decimal`][decimal.Decimal] types as strings.
 187 | You can use a custom serializer to override this behavior if desired. For example:
 188 | 
 189 | ```python
 190 | from decimal import Decimal
 191 | from typing import Annotated
 192 | 
 193 | from pydantic import BaseModel, PlainSerializer
 194 | 
 195 | 
 196 | class Model(BaseModel):
 197 |     x: Decimal
 198 |     y: Annotated[
 199 |         Decimal,
 200 |         PlainSerializer(
 201 |             lambda x: float(x), return_type=float, when_used='json'
 202 |         ),
 203 |     ]
 204 | 
 205 | 
 206 | my_model = Model(x=Decimal('1.1'), y=Decimal('2.1'))
 207 | 
 208 | print(my_model.model_dump())  # (1)!
 209 | #> {'x': Decimal('1.1'), 'y': Decimal('2.1')}
 210 | print(my_model.model_dump(mode='json'))  # (2)!
 211 | #> {'x': '1.1', 'y': 2.1}
 212 | print(my_model.model_dump_json())  # (3)!
 213 | #> {"x":"1.1","y":2.1}
 214 | ```
 215 | 
 216 | 1. Using [`model_dump`][pydantic.main.BaseModel.model_dump], both `x` and `y` remain instances of the `Decimal` type
 217 | 2. Using [`model_dump`][pydantic.main.BaseModel.model_dump] with `mode='json'`, `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
 218 | 3. Using [`model_dump_json`][pydantic.main.BaseModel.model_dump_json], `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
 219 | 
 220 | ### [`complex`][]
 221 | 
 222 | * Validation: Pydantic supports `complex` types or `str` values that can be converted to a `complex` type.
 223 | * Serialization: Pydantic serializes [`complex`][] types as strings.
 224 | 
 225 | ### [`fractions.Fraction`][fractions.Fraction]
 226 | 
 227 | * Validation: Pydantic attempts to convert the value to a `Fraction` using `Fraction(v)`.
 228 | * Serialization: Pydantic serializes [`Fraction`][fractions.Fraction] types as strings.
 229 | 
 230 | ## [`Enum`][enum.Enum]
 231 | 
 232 | Pydantic uses Python's standard [`enum`][] classes to define choices.
 233 | 
 234 | `enum.Enum` checks that the value is a valid `Enum` instance.
 235 | Subclass of `enum.Enum` checks that the value is a valid member of the enum.
 236 | 
 237 | ```python
 238 | from enum import Enum, IntEnum
 239 | 
 240 | from pydantic import BaseModel, ValidationError
 241 | 
 242 | 
 243 | class FruitEnum(str, Enum):
 244 |     pear = 'pear'
 245 |     banana = 'banana'
 246 | 
 247 | 
 248 | class ToolEnum(IntEnum):
 249 |     spanner = 1
 250 |     wrench = 2
 251 | 
 252 | 
 253 | class CookingModel(BaseModel):
 254 |     fruit: FruitEnum = FruitEnum.pear
 255 |     tool: ToolEnum = ToolEnum.spanner
 256 | 
 257 | 
 258 | print(CookingModel())
 259 | #> fruit=<FruitEnum.pear: 'pear'> tool=<ToolEnum.spanner: 1>
 260 | print(CookingModel(tool=2, fruit='banana'))
 261 | #> fruit=<FruitEnum.banana: 'banana'> tool=<ToolEnum.wrench: 2>
 262 | try:
 263 |     CookingModel(fruit='other')
 264 | except ValidationError as e:
 265 |     print(e)
 266 |     """
 267 |     1 validation error for CookingModel
 268 |     fruit
 269 |       Input should be 'pear' or 'banana' [type=enum, input_value='other', input_type=str]
 270 |     """
 271 | ```
 272 | 
 273 | ## Lists and Tuples
 274 | 
 275 | ### [`list`][]
 276 | 
 277 | Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`list`][].
 278 | When a generic parameter is provided, the appropriate validation is applied to all items of the list.
 279 | 
 280 | ```python
 281 | from typing import Optional
 282 | 
 283 | from pydantic import BaseModel
 284 | 
 285 | 
 286 | class Model(BaseModel):
 287 |     simple_list: Optional[list] = None
 288 |     list_of_ints: Optional[list[int]] = None
 289 | 
 290 | 
 291 | print(Model(simple_list=['1', '2', '3']).simple_list)
 292 | #> ['1', '2', '3']
 293 | print(Model(list_of_ints=['1', '2', '3']).list_of_ints)
 294 | #> [1, 2, 3]
 295 | ```
 296 | 
 297 | ### [`tuple`][]
 298 | 
 299 | Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`tuple`][].
 300 | When generic parameters are provided, the appropriate validation is applied to the respective items of the tuple
 301 | 
 302 | ### [`typing.Tuple`][]
 303 | 
 304 | Handled the same as `tuple` above.
 305 | 
 306 | ```python
 307 | from typing import Optional
 308 | 
 309 | from pydantic import BaseModel
 310 | 
 311 | 
 312 | class Model(BaseModel):
 313 |     simple_tuple: Optional[tuple] = None
 314 |     tuple_of_different_types: Optional[tuple[int, float, bool]] = None
 315 | 
 316 | 
 317 | print(Model(simple_tuple=[1, 2, 3, 4]).simple_tuple)
 318 | #> (1, 2, 3, 4)
 319 | print(Model(tuple_of_different_types=[3, 2, 1]).tuple_of_different_types)
 320 | #> (3, 2.0, True)
 321 | ```
 322 | 
 323 | ### [`typing.NamedTuple`][]
 324 | 
 325 | Subclasses of [`typing.NamedTuple`][] are similar to `tuple`, but create instances of the given `namedtuple` class.
 326 | 
 327 | Subclasses of [`collections.namedtuple`][] are similar to subclass of [`typing.NamedTuple`][], but since field types are not specified,
 328 | all fields are treated as having type [`Any`][typing.Any].
 329 | 
 330 | ```python
 331 | from typing import NamedTuple
 332 | 
 333 | from pydantic import BaseModel, ValidationError
 334 | 
 335 | 
 336 | class Point(NamedTuple):
 337 |     x: int
 338 |     y: int
 339 | 
 340 | 
 341 | class Model(BaseModel):
 342 |     p: Point
 343 | 
 344 | 
 345 | try:
 346 |     Model(p=('1.3', '2'))
 347 | except ValidationError as e:
 348 |     print(e)
 349 |     """
 350 |     1 validation error for Model
 351 |     p.0
 352 |       Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.3', input_type=str]
 353 |     """
 354 | ```
 355 | 
 356 | ## Deque
 357 | 
 358 | ### [`deque`][collections.deque]
 359 | 
 360 | Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`deque`][collections.deque].
 361 | When generic parameters are provided, the appropriate validation is applied to the respective items of the `deque`.
 362 | 
 363 | ### [`typing.Deque`][]
 364 | 
 365 | Handled the same as `deque` above.
 366 | 
 367 | ```python
 368 | from typing import Deque, Optional
 369 | 
 370 | from pydantic import BaseModel
 371 | 
 372 | 
 373 | class Model(BaseModel):
 374 |     deque: Optional[Deque[int]] = None
 375 | 
 376 | 
 377 | print(Model(deque=[1, 2, 3]).deque)
 378 | #> deque([1, 2, 3])
 379 | ```
 380 | 
 381 | ## Sets
 382 | 
 383 | ### [`set`][]
 384 | 
 385 | Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`set`][].
 386 | When a generic parameter is provided, the appropriate validation is applied to all items of the set.
 387 | 
 388 | ### [`typing.Set`][]
 389 | 
 390 | Handled the same as `set` above.
 391 | 
 392 | ```python
 393 | from typing import Optional, Set
 394 | 
 395 | from pydantic import BaseModel
 396 | 
 397 | 
 398 | class Model(BaseModel):
 399 |     simple_set: Optional[set] = None
 400 |     set_of_ints: Optional[Set[int]] = None
 401 | 
 402 | 
 403 | print(Model(simple_set={'1', '2', '3'}).simple_set)
 404 | #> {'1', '2', '3'}
 405 | print(Model(simple_set=['1', '2', '3']).simple_set)
 406 | #> {'1', '2', '3'}
 407 | print(Model(set_of_ints=['1', '2', '3']).set_of_ints)
 408 | #> {1, 2, 3}
 409 | ```
 410 | 
 411 | ### [`frozenset`][]
 412 | 
 413 | Allows [`list`][], [`tuple`][], [`set`][], [`frozenset`][], [`deque`][collections.deque], or generators and casts to a [`frozenset`][].
 414 | When a generic parameter is provided, the appropriate validation is applied to all items of the frozen set.
 415 | 
 416 | ### [`typing.FrozenSet`][]
 417 | 
 418 | Handled the same as `frozenset` above.
 419 | 
 420 | ```python
 421 | from typing import FrozenSet, Optional
 422 | 
 423 | from pydantic import BaseModel
 424 | 
 425 | 
 426 | class Model(BaseModel):
 427 |     simple_frozenset: Optional[frozenset] = None
 428 |     frozenset_of_ints: Optional[FrozenSet[int]] = None
 429 | 
 430 | 
 431 | m1 = Model(simple_frozenset=['1', '2', '3'])
 432 | print(type(m1.simple_frozenset))
 433 | #> <class 'frozenset'>
 434 | print(sorted(m1.simple_frozenset))
 435 | #> ['1', '2', '3']
 436 | 
 437 | m2 = Model(frozenset_of_ints=['1', '2', '3'])
 438 | print(type(m2.frozenset_of_ints))
 439 | #> <class 'frozenset'>
 440 | print(sorted(m2.frozenset_of_ints))
 441 | #> [1, 2, 3]
 442 | ```
 443 | 
 444 | ## Other Iterables
 445 | 
 446 | ### [`typing.Sequence`][]
 447 | 
 448 | This is intended for use when the provided value should meet the requirements of the `Sequence` ABC, and it is
 449 | desirable to do eager validation of the values in the container. Note that when validation must be performed on the
 450 | values of the container, the type of the container may not be preserved since validation may end up replacing values.
 451 | We guarantee that the validated value will be a valid [`typing.Sequence`][], but it may have a different type than was
 452 | provided (generally, it will become a `list`).
 453 | 
 454 | ### [`typing.Iterable`][]
 455 | 
 456 | This is intended for use when the provided value may be an iterable that shouldn't be consumed.
 457 | See [Infinite Generators](#infinite-generators) below for more detail on parsing and validation.
 458 | Similar to [`typing.Sequence`][], we guarantee that the validated result will be a valid [`typing.Iterable`][],
 459 | but it may have a different type than was provided. In particular, even if a non-generator type such as a `list`
 460 | is provided, the post-validation value of a field of type [`typing.Iterable`][] will be a generator.
 461 | 
 462 | Here is a simple example using [`typing.Sequence`][]:
 463 | 
 464 | ```python
 465 | from typing import Sequence
 466 | 
 467 | from pydantic import BaseModel
 468 | 
 469 | 
 470 | class Model(BaseModel):
 471 |     sequence_of_ints: Sequence[int] = None
 472 | 
 473 | 
 474 | print(Model(sequence_of_ints=[1, 2, 3, 4]).sequence_of_ints)
 475 | #> [1, 2, 3, 4]
 476 | print(Model(sequence_of_ints=(1, 2, 3, 4)).sequence_of_ints)
 477 | #> (1, 2, 3, 4)
 478 | ```
 479 | 
 480 | ### Infinite Generators
 481 | 
 482 | If you have a generator you want to validate, you can still use `Sequence` as described above.
 483 | In that case, the generator will be consumed and stored on the model as a list and its values will be
 484 | validated against the type parameter of the `Sequence` (e.g. `int` in `Sequence[int]`).
 485 | 
 486 | However, if you have a generator that you *don't* want to be eagerly consumed (e.g. an infinite
 487 | generator or a remote data loader), you can use a field of type [`Iterable`][typing.Iterable]:
 488 | 
 489 | ```python
 490 | from typing import Iterable
 491 | 
 492 | from pydantic import BaseModel
 493 | 
 494 | 
 495 | class Model(BaseModel):
 496 |     infinite: Iterable[int]
 497 | 
 498 | 
 499 | def infinite_ints():
 500 |     i = 0
 501 |     while True:
 502 |         yield i
 503 |         i += 1
 504 | 
 505 | 
 506 | m = Model(infinite=infinite_ints())
 507 | print(m)
 508 | """
 509 | infinite=ValidatorIterator(index=0, schema=Some(Int(IntValidator { strict: false })))
 510 | """
 511 | 
 512 | for i in m.infinite:
 513 |     print(i)
 514 |     #> 0
 515 |     #> 1
 516 |     #> 2
 517 |     #> 3
 518 |     #> 4
 519 |     #> 5
 520 |     #> 6
 521 |     #> 7
 522 |     #> 8
 523 |     #> 9
 524 |     #> 10
 525 |     if i == 10:
 526 |         break
 527 | ```
 528 | 
 529 | !!! warning
 530 |     During initial validation, `Iterable` fields only perform a simple check that the provided argument is iterable.
 531 |     To prevent it from being consumed, no validation of the yielded values is performed eagerly.
 532 | 
 533 | Though the yielded values are not validated eagerly, they are still validated when yielded, and will raise a
 534 | `ValidationError` at yield time when appropriate:
 535 | 
 536 | ```python
 537 | from typing import Iterable
 538 | 
 539 | from pydantic import BaseModel, ValidationError
 540 | 
 541 | 
 542 | class Model(BaseModel):
 543 |     int_iterator: Iterable[int]
 544 | 
 545 | 
 546 | def my_iterator():
 547 |     yield 13
 548 |     yield '27'
 549 |     yield 'a'
 550 | 
 551 | 
 552 | m = Model(int_iterator=my_iterator())
 553 | print(next(m.int_iterator))
 554 | #> 13
 555 | print(next(m.int_iterator))
 556 | #> 27
 557 | try:
 558 |     next(m.int_iterator)
 559 | except ValidationError as e:
 560 |     print(e)
 561 |     """
 562 |     1 validation error for ValidatorIterator
 563 |     2
 564 |       Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
 565 |     """
 566 | ```
 567 | 
 568 | ## Mapping Types
 569 | 
 570 | ### [`dict`][]
 571 | 
 572 | `dict(v)` is used to attempt to convert a dictionary.
 573 | 
 574 | ```python
 575 | from pydantic import BaseModel, ValidationError
 576 | 
 577 | 
 578 | class Model(BaseModel):
 579 |     x: dict[str, int]
 580 | 
 581 | 
 582 | m = Model(x={'foo': 1})
 583 | print(m.model_dump())
 584 | #> {'x': {'foo': 1}}
 585 | 
 586 | try:
 587 |     Model(x={'foo': '1'})
 588 | except ValidationError as e:
 589 |     print(e)
 590 |     """
 591 |     1 validation error for Model
 592 |     x
 593 |       Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
 594 |     """
 595 | ```
 596 | 
 597 | ### TypedDict
 598 | 
 599 | !!! note
 600 |     This is a new feature of the Python standard library as of Python 3.8.
 601 |     Because of limitations in [typing.TypedDict][] before 3.12, the [typing-extensions](https://pypi.org/project/typing-extensions/)
 602 |     package is required for Python <3.12. You'll need to import `TypedDict` from `typing_extensions` instead of `typing` and will
 603 |     get a build time error if you don't.
 604 | 
 605 | [`TypedDict`][typing.TypedDict] declares a dictionary type that expects all of
 606 | its instances to have a certain set of keys, where each key is associated with a value of a consistent type.
 607 | 
 608 | It is same as [`dict`][] but Pydantic will validate the dictionary since keys are annotated.
 609 | 
 610 | ```python
 611 | from typing_extensions import TypedDict
 612 | 
 613 | from pydantic import TypeAdapter, ValidationError
 614 | 
 615 | 
 616 | class User(TypedDict):
 617 |     name: str
 618 |     id: int
 619 | 
 620 | 
 621 | ta = TypeAdapter(User)
 622 | 
 623 | print(ta.validate_python({'name': 'foo', 'id': 1}))
 624 | #> {'name': 'foo', 'id': 1}
 625 | 
 626 | try:
 627 |     ta.validate_python({'name': 'foo'})
 628 | except ValidationError as e:
 629 |     print(e)
 630 |     """
 631 |     1 validation error for User
 632 |     id
 633 |       Field required [type=missing, input_value={'name': 'foo'}, input_type=dict]
 634 |     """
 635 | ```
 636 | 
 637 | You can define `__pydantic_config__` to change the model inherited from [`TypedDict`][typing.TypedDict].
 638 | See the [`ConfigDict` API reference][pydantic.config.ConfigDict] for more details.
 639 | 
 640 | ```python
 641 | from typing import Optional
 642 | 
 643 | from typing_extensions import TypedDict
 644 | 
 645 | from pydantic import ConfigDict, TypeAdapter, ValidationError
 646 | 
 647 | 
 648 | # `total=False` means keys are non-required
 649 | class UserIdentity(TypedDict, total=False):
 650 |     name: Optional[str]
 651 |     surname: str
 652 | 
 653 | 
 654 | class User(TypedDict):
 655 |     __pydantic_config__ = ConfigDict(extra='forbid')
 656 | 
 657 |     identity: UserIdentity
 658 |     age: int
 659 | 
 660 | 
 661 | ta = TypeAdapter(User)
 662 | 
 663 | print(
 664 |     ta.validate_python(
 665 |         {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}
 666 |     )
 667 | )
 668 | #> {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}
 669 | 
 670 | print(
 671 |     ta.validate_python(
 672 |         {'identity': {'name': None, 'surname': 'John'}, 'age': 37}
 673 |     )
 674 | )
 675 | #> {'identity': {'name': None, 'surname': 'John'}, 'age': 37}
 676 | 
 677 | print(ta.validate_python({'identity': {}, 'age': 37}))
 678 | #> {'identity': {}, 'age': 37}
 679 | 
 680 | 
 681 | try:
 682 |     ta.validate_python(
 683 |         {'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': 24}
 684 |     )
 685 | except ValidationError as e:
 686 |     print(e)
 687 |     """
 688 |     1 validation error for User
 689 |     identity.name
 690 |       Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
 691 |     """
 692 | 
 693 | try:
 694 |     ta.validate_python(
 695 |         {
 696 |             'identity': {'name': 'Smith', 'surname': 'John'},
 697 |             'age': '37',
 698 |             'email': 'john.smith@me.com',
 699 |         }
 700 |     )
 701 | except ValidationError as e:
 702 |     print(e)
 703 |     """
 704 |     1 validation error for User
 705 |     email
 706 |       Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
 707 |     """
 708 | ```
 709 | 
 710 | ## Callable
 711 | 
 712 | See below for more detail on parsing and validation
 713 | 
 714 | Fields can also be of type [`Callable`][typing.Callable]:
 715 | 
 716 | ```python
 717 | from typing import Callable
 718 | 
 719 | from pydantic import BaseModel
 720 | 
 721 | 
 722 | class Foo(BaseModel):
 723 |     callback: Callable[[int], int]
 724 | 
 725 | 
 726 | m = Foo(callback=lambda x: x)
 727 | print(m)
 728 | #> callback=<function <lambda> at 0x0123456789ab>
 729 | ```
 730 | 
 731 | !!! warning
 732 |     Callable fields only perform a simple check that the argument is
 733 |     callable; no validation of arguments, their types, or the return
 734 |     type is performed.
 735 | 
 736 | ## IP Address Types
 737 | 
 738 | * [`ipaddress.IPv4Address`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
 739 | * [`ipaddress.IPv4Interface`][]: Uses the type itself for validation by passing the value to `IPv4Address(v)`.
 740 | * [`ipaddress.IPv4Network`][]: Uses the type itself for validation by passing the value to `IPv4Network(v)`.
 741 | * [`ipaddress.IPv6Address`][]: Uses the type itself for validation by passing the value to `IPv6Address(v)`.
 742 | * [`ipaddress.IPv6Interface`][]: Uses the type itself for validation by passing the value to `IPv6Interface(v)`.
 743 | * [`ipaddress.IPv6Network`][]: Uses the type itself for validation by passing the value to `IPv6Network(v)`.
 744 | 
 745 | See [Network Types](../api/networks.md) for other custom IP address types.
 746 | 
 747 | ## UUID
 748 | 
 749 | For UUID, Pydantic tries to use the type itself for validation by passing the value to `UUID(v)`.
 750 | There's a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`.
 751 | 
 752 | In case you want to constrain the UUID version, you can check the following types:
 753 | 
 754 | * [`UUID1`][pydantic.types.UUID1]: requires UUID version 1.
 755 | * [`UUID3`][pydantic.types.UUID3]: requires UUID version 3.
 756 | * [`UUID4`][pydantic.types.UUID4]: requires UUID version 4.
 757 | * [`UUID5`][pydantic.types.UUID5]: requires UUID version 5.
 758 | 
 759 | ## Union
 760 | 
 761 | Pydantic has extensive support for union validation, both [`typing.Union`][] and Python 3.10's pipe syntax (`A | B`) are supported.
 762 | Read more in the [`Unions`](../concepts/unions.md) section of the concepts docs.
 763 | 
 764 | ## [`type`][]
 765 | 
 766 | Pydantic supports the use of `type[T]` to specify that a field may only accept classes (not instances)
 767 | that are subclasses of `T`.
 768 | 
 769 | ```python
 770 | from pydantic import BaseModel, ValidationError
 771 | 
 772 | 
 773 | class Foo:
 774 |     pass
 775 | 
 776 | 
 777 | class Bar(Foo):
 778 |     pass
 779 | 
 780 | 
 781 | class Other:
 782 |     pass
 783 | 
 784 | 
 785 | class SimpleModel(BaseModel):
 786 |     just_subclasses: type[Foo]
 787 | 
 788 | 
 789 | SimpleModel(just_subclasses=Foo)
 790 | SimpleModel(just_subclasses=Bar)
 791 | try:
 792 |     SimpleModel(just_subclasses=Other)
 793 | except ValidationError as e:
 794 |     print(e)
 795 |     """
 796 |     1 validation error for SimpleModel
 797 |     just_subclasses
 798 |       Input should be a subclass of Foo [type=is_subclass_of, input_value=<class '__main__.Other'>, input_type=type]
 799 |     """
 800 | ```
 801 | 
 802 | You may also use `type` to specify that any class is allowed.
 803 | 
 804 | ```python {upgrade="skip"}
 805 | from pydantic import BaseModel, ValidationError
 806 | 
 807 | 
 808 | class Foo:
 809 |     pass
 810 | 
 811 | 
 812 | class LenientSimpleModel(BaseModel):
 813 |     any_class_goes: type
 814 | 
 815 | 
 816 | LenientSimpleModel(any_class_goes=int)
 817 | LenientSimpleModel(any_class_goes=Foo)
 818 | try:
 819 |     LenientSimpleModel(any_class_goes=Foo())
 820 | except ValidationError as e:
 821 |     print(e)
 822 |     """
 823 |     1 validation error for LenientSimpleModel
 824 |     any_class_goes
 825 |       Input should be a type [type=is_type, input_value=<__main__.Foo object at 0x0123456789ab>, input_type=Foo]
 826 |     """
 827 | ```
 828 | 
 829 | ## [`typing.TypeVar`][]
 830 | 
 831 | [`TypeVar`][typing.TypeVar] is supported either unconstrained, constrained or with a bound.
 832 | 
 833 | ```python
 834 | from typing import TypeVar
 835 | 
 836 | from pydantic import BaseModel
 837 | 
 838 | Foobar = TypeVar('Foobar')
 839 | BoundFloat = TypeVar('BoundFloat', bound=float)
 840 | IntStr = TypeVar('IntStr', int, str)
 841 | 
 842 | 
 843 | class Model(BaseModel):
 844 |     a: Foobar  # equivalent of ": Any"
 845 |     b: BoundFloat  # equivalent of ": float"
 846 |     c: IntStr  # equivalent of ": Union[int, str]"
 847 | 
 848 | 
 849 | print(Model(a=[1], b=4.2, c='x'))
 850 | #> a=[1] b=4.2 c='x'
 851 | 
 852 | # a may be None
 853 | print(Model(a=None, b=1, c=1))
 854 | #> a=None b=1.0 c=1
 855 | ```
 856 | 
 857 | ## None Types
 858 | 
 859 | [`None`][], `type(None)`, or `Literal[None]` are all equivalent according to [the typing specification](https://typing.readthedocs.io/en/latest/spec/special-types.html#none).
 860 | Allows only `None` value.
 861 | 
 862 | ## Strings
 863 | 
 864 | * [`str`][]: Strings are accepted as-is.
 865 | * [`bytes`][] and [`bytearray`][] are converted using the [`decode()`][bytes.decode] method.
 866 | * Enums inheriting from [`str`][] are converted using the [`value`][enum.Enum.value] attribute.
 867 | 
 868 | All other types cause an error.
 869 | <!-- * TODO: add note about optional number to string conversion from lig's PR -->
 870 | 
 871 | !!! warning "Strings aren't Sequences"
 872 | 
 873 |     While instances of `str` are technically valid instances of the `Sequence[str]` protocol from a type-checker's point of
 874 |     view, this is frequently not intended as is a common source of bugs.
 875 | 
 876 |     As a result, Pydantic raises a `ValidationError` if you attempt to pass a `str` or `bytes` instance into a field of type
 877 |     `Sequence[str]` or `Sequence[bytes]`:
 878 | 
 879 | ```python
 880 | from typing import Optional, Sequence
 881 | 
 882 | from pydantic import BaseModel, ValidationError
 883 | 
 884 | 
 885 | class Model(BaseModel):
 886 |     sequence_of_strs: Optional[Sequence[str]] = None
 887 |     sequence_of_bytes: Optional[Sequence[bytes]] = None
 888 | 
 889 | 
 890 | print(Model(sequence_of_strs=['a', 'bc']).sequence_of_strs)
 891 | #> ['a', 'bc']
 892 | print(Model(sequence_of_strs=('a', 'bc')).sequence_of_strs)
 893 | #> ('a', 'bc')
 894 | print(Model(sequence_of_bytes=[b'a', b'bc']).sequence_of_bytes)
 895 | #> [b'a', b'bc']
 896 | print(Model(sequence_of_bytes=(b'a', b'bc')).sequence_of_bytes)
 897 | #> (b'a', b'bc')
 898 | 
 899 | 
 900 | try:
 901 |     Model(sequence_of_strs='abc')
 902 | except ValidationError as e:
 903 |     print(e)
 904 |     """
 905 |     1 validation error for Model
 906 |     sequence_of_strs
 907 |       'str' instances are not allowed as a Sequence value [type=sequence_str, input_value='abc', input_type=str]
 908 |     """
 909 | try:
 910 |     Model(sequence_of_bytes=b'abc')
 911 | except ValidationError as e:
 912 |     print(e)
 913 |     """
 914 |     1 validation error for Model
 915 |     sequence_of_bytes
 916 |       'bytes' instances are not allowed as a Sequence value [type=sequence_str, input_value=b'abc', input_type=bytes]
 917 |     """
 918 | ```
 919 | 
 920 | ## Bytes
 921 | 
 922 | [`bytes`][] are accepted as-is. [`bytearray`][] is converted using `bytes(v)`. `str` are converted using `v.encode()`. `int`, `float`, and `Decimal` are coerced using `str(v).encode()`. See [ByteSize](types.md#pydantic.types.ByteSize) for more details.
 923 | 
 924 | ## [`typing.Literal`][]
 925 | 
 926 | Pydantic supports the use of [`typing.Literal`][] as a lightweight way to specify that a field may accept only specific literal values:
 927 | 
 928 | ```python
 929 | from typing import Literal
 930 | 
 931 | from pydantic import BaseModel, ValidationError
 932 | 
 933 | 
 934 | class Pie(BaseModel):
 935 |     flavor: Literal['apple', 'pumpkin']
 936 | 
 937 | 
 938 | Pie(flavor='apple')
 939 | Pie(flavor='pumpkin')
 940 | try:
 941 |     Pie(flavor='cherry')
 942 | except ValidationError as e:
 943 |     print(str(e))
 944 |     """
 945 |     1 validation error for Pie
 946 |     flavor
 947 |       Input should be 'apple' or 'pumpkin' [type=literal_error, input_value='cherry', input_type=str]
 948 |     """
 949 | ```
 950 | 
 951 | One benefit of this field type is that it can be used to check for equality with one or more specific values
 952 | without needing to declare custom validators:
 953 | 
 954 | ```python
 955 | from typing import ClassVar, Literal, Union
 956 | 
 957 | from pydantic import BaseModel, ValidationError
 958 | 
 959 | 
 960 | class Cake(BaseModel):
 961 |     kind: Literal['cake']
 962 |     required_utensils: ClassVar[list[str]] = ['fork', 'knife']
 963 | 
 964 | 
 965 | class IceCream(BaseModel):
 966 |     kind: Literal['icecream']
 967 |     required_utensils: ClassVar[list[str]] = ['spoon']
 968 | 
 969 | 
 970 | class Meal(BaseModel):
 971 |     dessert: Union[Cake, IceCream]
 972 | 
 973 | 
 974 | print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
 975 | #> Cake
 976 | print(type(Meal(dessert={'kind': 'icecream'}).dessert).__name__)
 977 | #> IceCream
 978 | try:
 979 |     Meal(dessert={'kind': 'pie'})
 980 | except ValidationError as e:
 981 |     print(str(e))
 982 |     """
 983 |     2 validation errors for Meal
 984 |     dessert.Cake.kind
 985 |       Input should be 'cake' [type=literal_error, input_value='pie', input_type=str]
 986 |     dessert.IceCream.kind
 987 |       Input should be 'icecream' [type=literal_error, input_value='pie', input_type=str]
 988 |     """
 989 | ```
 990 | 
 991 | With proper ordering in an annotated `Union`, you can use this to parse types of decreasing specificity:
 992 | 
 993 | ```python
 994 | from typing import Literal, Optional, Union
 995 | 
 996 | from pydantic import BaseModel
 997 | 
 998 | 
 999 | class Dessert(BaseModel):
1000 |     kind: str
1001 | 
1002 | 
1003 | class Pie(Dessert):
1004 |     kind: Literal['pie']
1005 |     flavor: Optional[str]
1006 | 
1007 | 
1008 | class ApplePie(Pie):
1009 |     flavor: Literal['apple']
1010 | 
1011 | 
1012 | class PumpkinPie(Pie):
1013 |     flavor: Literal['pumpkin']
1014 | 
1015 | 
1016 | class Meal(BaseModel):
1017 |     dessert: Union[ApplePie, PumpkinPie, Pie, Dessert]
1018 | 
1019 | 
1020 | print(type(Meal(dessert={'kind': 'pie', 'flavor': 'apple'}).dessert).__name__)
1021 | #> ApplePie
1022 | print(type(Meal(dessert={'kind': 'pie', 'flavor': 'pumpkin'}).dessert).__name__)
1023 | #> PumpkinPie
1024 | print(type(Meal(dessert={'kind': 'pie'}).dessert).__name__)
1025 | #> Dessert
1026 | print(type(Meal(dessert={'kind': 'cake'}).dessert).__name__)
1027 | #> Dessert
1028 | ```
1029 | 
1030 | ## [`typing.Any`][]
1031 | 
1032 | Allows any value, including `None`.
1033 | 
1034 | ## [`typing.Hashable`][]
1035 | 
1036 | * From Python, supports any data that passes an `isinstance(v, Hashable)` check.
1037 | * From JSON, first loads the data via an `Any` validator, then checks if the data is hashable with `isinstance(v, Hashable)`.
1038 | 
1039 | ## [`typing.Annotated`][]
1040 | 
1041 | Allows wrapping another type with arbitrary metadata, as per [PEP-593](https://www.python.org/dev/peps/pep-0593/). The `Annotated` hint may contain a single call to the [`Field` function](../concepts/types.md#using-the-annotated-pattern), but otherwise the additional metadata is ignored and the root type is used.
1042 | 
1043 | ## [`typing.Pattern`][]
1044 | 
1045 | Will cause the input value to be passed to `re.compile(v)` to create a regular expression pattern.
1046 | 
1047 | ## [`pathlib.Path`][]
1048 | 
1049 | Simply uses the type itself for validation by passing the value to `Path(v)`.
1050 | 


--------------------------------------------------------------------------------
/docs/api/type_adapter.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.type_adapter.TypeAdapter
2 | 


--------------------------------------------------------------------------------
/docs/api/types.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.types
2 |     options:
3 |         show_root_heading: true
4 |         merge_init_into_class: false
5 | 


--------------------------------------------------------------------------------
/docs/api/validate_call.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.validate_call_decorator
2 | 


--------------------------------------------------------------------------------
/docs/api/version.md:
--------------------------------------------------------------------------------
1 | ::: pydantic.__version__
2 |     options:
3 |         show_root_heading: true
4 | 
5 | ::: pydantic.version.version_info
6 |     options:
7 |         show_root_heading: true
8 | 


--------------------------------------------------------------------------------